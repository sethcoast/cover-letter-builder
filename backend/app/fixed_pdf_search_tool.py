from typing import Any, Optional, Type

from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel
from pydantic import model_validator
from crewai_tools.tools.rag.rag_tool import RagTool
from crewai_tools.tools.pdf_search_tool.pdf_search_tool import PDFSearchToolSchema, FixedPDFSearchToolSchema


from embedchain import App

from crewai_tools.tools.rag.rag_tool import Adapter


class PDFEmbedchainAdapter(Adapter):
    embedchain_app: App
    summarize: bool = False
    src: Optional[str] = None

    def query(self, question: str) -> str:
        print("Querying pdf from embedchain")
        print("pdf source: ", self.src)
        where = {"app_id": self.embedchain_app.config.id, "source": self.src} if self.src else None
        result, sources = self.embedchain_app.query(
            # todo: this where clause is not working for some reason
            question, citations=True, dry_run=(not self.summarize), where=where
        )
        if self.summarize:
            return result
        return "\n\n".join([source[0] for source in sources])

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        print("Adding pdf to embedchain")
        print("pdf source: ", args[0])
        self.src = args[0]
        self.embedchain_app.add(*args, **kwargs)

class FixedPDFSearchTool(RagTool):
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
        
            
    @model_validator(mode="after")
    def _set_default_adapter(self):
        if isinstance(self.adapter, RagTool._AdapterPlaceholder):
            app = App.from_config(config=self.config) if self.config else App()
            self.adapter = PDFEmbedchainAdapter(
                embedchain_app=app, summarize=self.summarize
            )

        return self

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