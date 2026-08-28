"""
AI recommendation agent -- takes ranked site data and generates a
human-readable recommendation using Groq's LLM.

Includes a self-check (evaluator-optimizer) step: after the first
recommendation is generated, a second pass checks it against the raw
numbers for consistency (e.g. flags if the LLM called an extreme-loss
site "great" without mentioning the risk). If the check fails, the
agent is re-prompted with the discrepancy and asked to fix it -- same
pattern used in DocuVeritas's self-correction loop.
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a solar installation advisor for SolarShield, an AI \
tool that helps homeowners and businesses decide where to install solar panels \
based on real hyperlocal temperature and solar irradiance data.

You will be given a ranked list of candidate sites, each with measured ambient \
temperature, solar irradiance (GHI), heat-driven efficiency loss %, and actual \
usable power output.

Write a clear, decision-ready recommendation. Respond ONLY with valid JSON in \
this exact shape, no markdown, no preamble:

{
  "best_site": "<name of the top-ranked site>",
  "summary": "<2-3 sentence plain-English recommendation explaining WHY this site \
is best, citing specific numbers (temperature, output, loss %)>",
  "per_site_notes": [
    {"name": "<site name>", "note": "<1 sentence -- why it ranked where it did>"}
  ],
  "risk_flags": ["<any site with 'extreme' or 'high' risk_level, with a 1-line \
caution>"]
}
"""

FIX_PROMPT_TEMPLATE = """Your previous recommendation had a consistency problem: \
{issue}

Here is your previous JSON output:
{previous_output}

Here is the original site data again:
{site_data}

Fix the issue and return corrected JSON in the exact same shape. Respond ONLY \
with valid JSON, no markdown, no preamble."""


def _trim_sites(ranked_sites: list[dict]) -> list[dict]:
    return [
        {
            "rank": s["rank"],
            "name": s["name"],
            "temperature_f": s["temperature_f"],
            "ghi_w_m2": s["ghi"],
            "efficiency_loss_percent": s["efficiency_loss_percent"],
            "actual_output_kw": s["actual_output_kw"],
            "dollar_lost_per_year": s["dollar_lost_per_year"],
            "risk_level": s["risk_level"],
        }
        for s in ranked_sites
    ]


def _call_llm(messages: list[dict]) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)


def _self_check(recommendation: dict, trimmed_sites: list[dict]) -> str | None:
    """
    Returns a description of the problem if the recommendation is
    inconsistent with the raw data, or None if it looks fine.
    """
    best_name = recommendation.get("best_site")
    best_site_data = next((s for s in trimmed_sites if s["name"] == best_name), None)

    if best_site_data is None:
        return f"best_site '{best_name}' doesn't match any site name in the data."

    if best_site_data["rank"] != 1:
        return (f"best_site is '{best_name}' (rank {best_site_data['rank']}), "
                f"but rank 1 should be the recommended site.")

    if best_site_data["risk_level"] in ("high", "extreme") and not recommendation.get("risk_flags"):
        return (f"The recommended site '{best_name}' has risk_level "
                f"'{best_site_data['risk_level']}' but risk_flags is empty -- "
                f"this should be flagged for the user.")

    return None


def generate_recommendation(ranked_sites: list[dict], max_fix_attempts: int = 2) -> dict:
    """
    ranked_sites: output of site_ranker.rank_sites().
    Returns the JSON shape described in SYSTEM_PROMPT, self-checked
    against the raw numbers before being returned.
    """
    trimmed = _trim_sites(ranked_sites)
    site_data_json = json.dumps(trimmed, indent=2)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": site_data_json},
    ]
    recommendation = _call_llm(messages)

    for attempt in range(max_fix_attempts):
        issue = _self_check(recommendation, trimmed)
        if issue is None:
            recommendation["_self_check"] = "passed"
            return recommendation

        fix_prompt = FIX_PROMPT_TEMPLATE.format(
            issue=issue,
            previous_output=json.dumps(recommendation, indent=2),
            site_data=site_data_json,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": fix_prompt},
        ]
        recommendation = _call_llm(messages)

    recommendation["_self_check"] = "failed_after_retries"
    return recommendation


if __name__ == "__main__":
    fake_ranked = [
        {"rank": 1, "name": "San Diego, CA", "temperature_f": 78.0,
         "ghi": 780.0, "efficiency_loss_percent": 4.2, "actual_output_kw": 4.9,
         "dollar_lost_per_year": 65.0, "risk_level": "low"},
        {"rank": 2, "name": "Phoenix, AZ", "temperature_f": 108.5,
         "ghi": 850.0, "efficiency_loss_percent": 15.8, "actual_output_kw": 4.29,
         "dollar_lost_per_year": 323.5, "risk_level": "extreme"},
    ]
    result = generate_recommendation(fake_ranked)
    print(json.dumps(result, indent=2))