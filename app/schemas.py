from pydantic import BaseModel, Field


class SourceView(BaseModel):
    key: str
    name: str
    base_url: str
    region: str = ""
    enabled: bool = True


class SearchResult(BaseModel):
    id: int
    title: str
    url: str
    publish_time: str = ""
    issuer: str = ""
    channel: str = ""
    snippet: str = ""


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)


class Citation(BaseModel):
    id: int | None = None
    title: str
    url: str
    publish_time: str = ""
    issuer: str = ""
    snippet: str = ""


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]


class PolicyExtraction(BaseModel):
    policy_name: str = ""
    issuer: str = ""
    publish_time: str = ""
    location: str = ""
    eligible_audience: list[str] = Field(default_factory=list)
    support_items: list[str] = Field(default_factory=list)
    application_materials: list[str] = Field(default_factory=list)
    application_process: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    contact_points: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    summary: str = ""
    source_url: str = ""


class IngestRequest(BaseModel):
    source_keys: list[str] | None = None
    limit_per_channel: int = Field(default=10, ge=1, le=100)


class IngestResponse(BaseModel):
    sources: dict


class SourceChannelInput(BaseModel):
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    item_selector: str = Field(default="a", min_length=1)
    link_selector: str = Field(default="a", min_length=1)
    list_date_selector: str = ""
    issuer: str = ""


class SourceCreateRequest(BaseModel):
    key: str = ""
    name: str = Field(min_length=1)
    base_url: str = ""
    region: str = ""
    enabled: bool = True
    crawler: str = "generic_gov"
    channels: list[SourceChannelInput] = Field(min_length=1)


class SourceDiscoverRequest(BaseModel):
    url: str = Field(min_length=8)


class SourcePreviewItem(BaseModel):
    title: str
    url: str
    publish_time: str = ""


class SourceDiscoverResponse(BaseModel):
    item_selector: str
    link_selector: str
    list_date_selector: str = ""
    previews: list[SourcePreviewItem]
