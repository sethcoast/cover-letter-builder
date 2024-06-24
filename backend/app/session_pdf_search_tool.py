from typing import Any, Optional, Type

from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, model_validator
from crewai_tools.tools.rag.rag_tool import RagTool
from crewai_tools.tools.pdf_search_tool.pdf_search_tool import PDFSearchToolSchema, FixedPDFSearchToolSchema


from embedchain import App

from crewai_tools.tools.rag.rag_tool import Adapter


class SessionEmbedchainAdapter(Adapter):
    embedchain_app: App
    summarize: bool = False

    def query(self, question: str) -> str:
        result, sources = self.embedchain_app.query(
            question, citations=True, dry_run=(not self.summarize)
        )
        if self.summarize:
            return result
        return "\n\n".join([source[0] for source in sources])

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.embedchain_app.add(*args, **kwargs)

class SessionPDFSearchTool(RagTool):
    name: str = "Search a PDF's content"
    description: str = (
        "A tool that can be used to semantic search a query from a PDF's content."
    )
    args_schema: Type[BaseModel] = PDFSearchToolSchema

    def __init__(self, pdf: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        
        if pdf is not None:
            self.add(pdf)
            self.description = f"A tool that can be used to semantic search a query the {pdf} PDF's content."
            self.args_schema = FixedPDFSearchToolSchema
            self._generate_description()
        
            
    # @model_validator(mode="after")
    # def _set_default_adapter(self):
    #     if isinstance(self.adapter, RagTool._AdapterPlaceholder):
    #         app = App.from_config(config=self.config) if self.config else App()
    #         self.adapter = SessionEmbedchainAdapter(
    #             embedchain_app=app, summarize=self.summarize
    #         )

    #     return self

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        kwargs["data_type"] = DataType.PDF_FILE
        super().add(*args, **kwargs)

    def _before_run(
        self,
        query: str,
        **kwargs: Any,
    ) -> Any:
        if "pdf" in kwargs:
            self.add(kwargs["pdf"])