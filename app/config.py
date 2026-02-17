from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Outreach Bot"
    environment: str = "development"

    serpapi_key: str | None = None

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2024-02-15-preview"
    azure_openai_deployment: str | None = None

    azure_storage_connection_string: str | None = None
    storage_campaigns_table: str = "campaigns"
    storage_leads_table: str = "leads"
    storage_outreach_table: str = "outreach"

    acs_email_connection_string: str | None = None
    acs_email_sender: str | None = None

    sender_name: str = "Your Name"
    sender_title: str = "Founder"
    sender_company: str = "Your Company"
    sender_value_prop: str = "We help teams improve outbound efficiency."

    web_results_per_query: int = 5
    max_pages_to_fetch: int = 10


settings = Settings()
