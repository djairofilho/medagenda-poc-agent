"""Optional qualitative judge for synthetic experiments only."""

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage


class QualityRating(BaseModel):
    clarity: int = Field(ge=1, le=5)
    instruction_adherence: int = Field(ge=1, le=5)


def judge_reply(reply: str) -> dict[str, int]:
    from app.conversations.llm import LangChainModel

    model = LangChainModel()._get_model().with_structured_output(QualityRating)
    rating = model.invoke([
        SystemMessage(content=(
            "Avalie somente a resposta sintética de uma recepção médica. "
            "Clareza: 1 a 5. Aderência: 1 a 5, sem diagnóstico e sem afirmar agendamento não gravado. "
            "Não faça avaliação clínica."
        )),
        HumanMessage(content=reply),
    ])
    return {"clarity": rating.clarity, "instruction_adherence": rating.instruction_adherence}


def quality_score(*, output, **kwargs):
    from langfuse import Evaluation

    rating = output["quality"]
    return Evaluation(
        name="judge_quality", value=(rating["clarity"] + rating["instruction_adherence"]) / 10,
        comment=f"Clareza={rating['clarity']}; aderência={rating['instruction_adherence']}.",
    )
