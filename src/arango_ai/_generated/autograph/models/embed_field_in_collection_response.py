from typing import TYPE_CHECKING, Any, BinaryIO, Optional, TextIO, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EmbedFieldInCollectionResponse")


@_attrs_define
class EmbedFieldInCollectionResponse:
    """EmbedFieldInCollectionResponse contains the result of the embed operation.

    Attributes:
        status (Union[Unset, str]):
        message (Union[Unset, str]):
        collection (Union[Unset, str]):
        field (Union[Unset, str]):
        embedding_field (Union[Unset, str]):
        documents_updated (Union[Unset, int]):
        documents_skipped (Union[Unset, int]):
        documents_examined (Union[Unset, int]):
        documents_failed (Union[Unset, int]):
        documents_ineligible (Union[Unset, int]):
    """

    status: Union[Unset, str] = UNSET
    message: Union[Unset, str] = UNSET
    collection: Union[Unset, str] = UNSET
    field: Union[Unset, str] = UNSET
    embedding_field: Union[Unset, str] = UNSET
    documents_updated: Union[Unset, int] = UNSET
    documents_skipped: Union[Unset, int] = UNSET
    documents_examined: Union[Unset, int] = UNSET
    documents_failed: Union[Unset, int] = UNSET
    documents_ineligible: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        message = self.message

        collection = self.collection

        field = self.field

        embedding_field = self.embedding_field

        documents_updated = self.documents_updated

        documents_skipped = self.documents_skipped

        documents_examined = self.documents_examined

        documents_failed = self.documents_failed

        documents_ineligible = self.documents_ineligible

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if message is not UNSET:
            field_dict["message"] = message
        if collection is not UNSET:
            field_dict["collection"] = collection
        if field is not UNSET:
            field_dict["field"] = field
        if embedding_field is not UNSET:
            field_dict["embeddingField"] = embedding_field
        if documents_updated is not UNSET:
            field_dict["documentsUpdated"] = documents_updated
        if documents_skipped is not UNSET:
            field_dict["documentsSkipped"] = documents_skipped
        if documents_examined is not UNSET:
            field_dict["documentsExamined"] = documents_examined
        if documents_failed is not UNSET:
            field_dict["documentsFailed"] = documents_failed
        if documents_ineligible is not UNSET:
            field_dict["documentsIneligible"] = documents_ineligible

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        status = d.pop("status", UNSET)

        message = d.pop("message", UNSET)

        collection = d.pop("collection", UNSET)

        field = d.pop("field", UNSET)

        embedding_field = d.pop("embeddingField", UNSET)

        documents_updated = d.pop("documentsUpdated", UNSET)

        documents_skipped = d.pop("documentsSkipped", UNSET)

        documents_examined = d.pop("documentsExamined", UNSET)

        documents_failed = d.pop("documentsFailed", UNSET)

        documents_ineligible = d.pop("documentsIneligible", UNSET)

        embed_field_in_collection_response = cls(
            status=status,
            message=message,
            collection=collection,
            field=field,
            embedding_field=embedding_field,
            documents_updated=documents_updated,
            documents_skipped=documents_skipped,
            documents_examined=documents_examined,
            documents_failed=documents_failed,
            documents_ineligible=documents_ineligible,
        )

        embed_field_in_collection_response.additional_properties = d
        return embed_field_in_collection_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
