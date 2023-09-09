from typing import Annotated

from pydantic import AliasPath, BaseModel, Field


class UserFromCults(BaseModel):
    nickname: Annotated[str, Field(validation_alias="nick")]


class IllustrationsFromCults(BaseModel):
    src: Annotated[str, Field(validation_alias="imageUrl")]


class AssetFromCults(BaseModel):
    name: str
    slug: str
    details: str
    description: str
    cents: Annotated[int, Field(validation_alias=AliasPath("price", "cents"))]
    creator: UserFromCults
    illustrations: list[IllustrationsFromCults]
    tags: list[str]


class OrderFromCults(BaseModel):
    creation: AssetFromCults
    download_url: Annotated[str, Field(validation_alias="downloadUrl")]
