from __future__ import annotations

from typing import Any

import pandas as pd


class HubSpotDeduper:
    def __init__(self, client: Any) -> None:
        self.client = client

    def deduplicate_leads(
        self,
        df: pd.DataFrame,
        rate_limiter: Any = None,
    ) -> tuple[pd.DataFrame, dict]:
        from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest

        stats = {
            "total_input": len(df),
            "duplicates_by_email": 0,
            "duplicates_by_name": 0,
            "net_new": 0,
            "errors": 0,
        }
        duplicate_indices: set[int] = set()

        if "email" in df.columns:
            emails_with_idx = [
                (idx, str(row["email"]).strip().lower())
                for idx, row in df.iterrows()
                if pd.notna(row.get("email")) and str(row["email"]).strip()
            ]

            for i in range(0, len(emails_with_idx), 5):
                batch = emails_with_idx[i : i + 5]
                if rate_limiter:
                    rate_limiter.wait_if_needed("hubspot")

                try:
                    search_request = PublicObjectSearchRequest(
                        filter_groups=[
                            FilterGroup(
                                filters=[Filter(property_name="email", operator="EQ", value=email)],
                            )
                            for _idx, email in batch
                        ],
                        properties=["email"],
                        limit=len(batch),
                    )
                    result = self.client.crm.contacts.search_api.do_search(
                        public_object_search_request=search_request,
                    )
                    found_emails = {
                        item.properties.get("email", "").lower()
                        for item in result.results
                        if item.properties.get("email")
                    }
                    for idx, email in batch:
                        if email in found_emails:
                            duplicate_indices.add(idx)
                            stats["duplicates_by_email"] += 1
                except Exception:
                    stats["errors"] += 1

        for idx in [row_idx for row_idx in df.index if row_idx not in duplicate_indices]:
            row = df.loc[idx]
            first_name = str(row.get("first_name", "")).strip()
            last_name = str(row.get("last_name", "")).strip()
            domain = str(row.get("domain", "")).strip()
            if not first_name or not last_name or not domain:
                continue

            if rate_limiter:
                rate_limiter.wait_if_needed("hubspot")

            try:
                search_request = PublicObjectSearchRequest(
                    filter_groups=[
                        FilterGroup(
                            filters=[
                                Filter(property_name="firstname", operator="EQ", value=first_name),
                                Filter(property_name="lastname", operator="EQ", value=last_name),
                            ],
                        )
                    ],
                    properties=["firstname", "lastname", "associatedcompanyid"],
                    limit=5,
                )
                result = self.client.crm.contacts.search_api.do_search(
                    public_object_search_request=search_request,
                )
                if any(self._contact_matches_domain(contact_result.id, domain) for contact_result in result.results):
                    duplicate_indices.add(idx)
                    stats["duplicates_by_name"] += 1
            except Exception:
                stats["errors"] += 1

        filtered_df = df.drop(index=list(duplicate_indices))
        stats["net_new"] = len(filtered_df)
        return filtered_df, stats

    def _contact_matches_domain(self, contact_id: str, domain: str) -> bool:
        try:
            associations = self.client.crm.contacts.associations_api.get_all(
                contact_id=contact_id,
                to_object_type="companies",
            )
        except Exception:
            return False

        for association in associations.results:
            try:
                company = self.client.crm.companies.basic_api.get_by_id(
                    company_id=association.id,
                    properties=["domain"],
                )
            except Exception:
                continue

            company_domain = (company.properties.get("domain") or "").lower().strip()
            normalized_domain = domain.lower().strip()
            if company_domain and (
                company_domain == normalized_domain
                or company_domain.endswith("." + normalized_domain)
                or normalized_domain.endswith("." + company_domain)
            ):
                return True
        return False
