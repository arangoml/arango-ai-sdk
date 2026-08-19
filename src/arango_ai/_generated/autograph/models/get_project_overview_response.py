from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import Union

if TYPE_CHECKING:
    from ..models.category_overview import CategoryOverview
    from ..models.corpus_graph_overview import CorpusGraphOverview
    from ..models.knowledge_graph_overview import KnowledgeGraphOverview
    from ..models.strategies_overview import StrategiesOverview


T = TypeVar("T", bound="GetProjectOverviewResponse")


@_attrs_define
class GetProjectOverviewResponse:
    """GetProjectOverviewResponse contains the Project Overview aggregate read.

    Attributes:
        project (Union[Unset, str]):
        corpus_graph (Union[Unset, CorpusGraphOverview]): CorpusGraphOverview describes the corpus graph card on the
            Overview page.
        knowledge_graph (Union[Unset, KnowledgeGraphOverview]): KnowledgeGraphOverview describes the knowledge graph
            card on the Overview page.
        strategies (Union[Unset, StrategiesOverview]): StrategiesOverview describes the strategies block on the Overview
            page.
        categories (Union[Unset, list['CategoryOverview']]):
        category_count (Union[Unset, int]):
        total_documents (Union[Unset, int]):
        filtered_total_documents (Union[Unset, int]):
    """

    project: Union[Unset, str] = UNSET
    corpus_graph: Union[Unset, "CorpusGraphOverview"] = UNSET
    knowledge_graph: Union[Unset, "KnowledgeGraphOverview"] = UNSET
    strategies: Union[Unset, "StrategiesOverview"] = UNSET
    categories: Union[Unset, list["CategoryOverview"]] = UNSET
    category_count: Union[Unset, int] = UNSET
    total_documents: Union[Unset, int] = UNSET
    filtered_total_documents: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = self.project

        corpus_graph: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.corpus_graph, Unset):
            corpus_graph = self.corpus_graph.to_dict()

        knowledge_graph: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.knowledge_graph, Unset):
            knowledge_graph = self.knowledge_graph.to_dict()

        strategies: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.strategies, Unset):
            strategies = self.strategies.to_dict()

        categories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.categories, Unset):
            categories = []
            for categories_item_data in self.categories:
                categories_item = categories_item_data.to_dict()
                categories.append(categories_item)

        category_count = self.category_count

        total_documents = self.total_documents

        filtered_total_documents = self.filtered_total_documents

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project is not UNSET:
            field_dict["project"] = project
        if corpus_graph is not UNSET:
            field_dict["corpusGraph"] = corpus_graph
        if knowledge_graph is not UNSET:
            field_dict["knowledgeGraph"] = knowledge_graph
        if strategies is not UNSET:
            field_dict["strategies"] = strategies
        if categories is not UNSET:
            field_dict["categories"] = categories
        if category_count is not UNSET:
            field_dict["categoryCount"] = category_count
        if total_documents is not UNSET:
            field_dict["totalDocuments"] = total_documents
        if filtered_total_documents is not UNSET:
            field_dict["filteredTotalDocuments"] = filtered_total_documents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.category_overview import CategoryOverview
        from ..models.corpus_graph_overview import CorpusGraphOverview
        from ..models.knowledge_graph_overview import KnowledgeGraphOverview
        from ..models.strategies_overview import StrategiesOverview

        d = src_dict.copy()
        project = d.pop("project", UNSET)

        _corpus_graph = d.pop("corpusGraph", UNSET)
        corpus_graph: Union[Unset, CorpusGraphOverview]
        if isinstance(_corpus_graph, Unset):
            corpus_graph = UNSET
        else:
            corpus_graph = CorpusGraphOverview.from_dict(_corpus_graph)

        _knowledge_graph = d.pop("knowledgeGraph", UNSET)
        knowledge_graph: Union[Unset, KnowledgeGraphOverview]
        if isinstance(_knowledge_graph, Unset):
            knowledge_graph = UNSET
        else:
            knowledge_graph = KnowledgeGraphOverview.from_dict(_knowledge_graph)

        _strategies = d.pop("strategies", UNSET)
        strategies: Union[Unset, StrategiesOverview]
        if isinstance(_strategies, Unset):
            strategies = UNSET
        else:
            strategies = StrategiesOverview.from_dict(_strategies)

        categories = []
        _categories = d.pop("categories", UNSET)
        for categories_item_data in _categories or []:
            categories_item = CategoryOverview.from_dict(categories_item_data)

            categories.append(categories_item)

        category_count = d.pop("categoryCount", UNSET)

        total_documents = d.pop("totalDocuments", UNSET)

        filtered_total_documents = d.pop("filteredTotalDocuments", UNSET)

        get_project_overview_response = cls(
            project=project,
            corpus_graph=corpus_graph,
            knowledge_graph=knowledge_graph,
            strategies=strategies,
            categories=categories,
            category_count=category_count,
            total_documents=total_documents,
            filtered_total_documents=filtered_total_documents,
        )

        get_project_overview_response.additional_properties = d
        return get_project_overview_response

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
