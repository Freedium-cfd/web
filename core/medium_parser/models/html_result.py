from dataclasses import dataclass


@dataclass
class HtmlResult:
    title: str
    description: str
    url: str
    data: str
