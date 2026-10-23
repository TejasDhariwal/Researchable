from django.shortcuts import render
from django.http import FileResponse, Http404
from django.views.decorators.http import require_http_methods
from pathlib import Path
from coreApp.services.work_flow import WorkFlow
from coreApp.services.presentation import create_presentation
from .models import *

# Create your views here.

def research_output(request):
    """ This takes in the user data and generates the research, presentation and summary. """
    # fetch the form data
    requirements = request.session.get("research_requirements")

    # creating output
    flow = WorkFlow()
    
    # 1. Generate the plan
    plan = flow.generate_plan(requirements)
    
    # 2. Search once and get candidate sources
    search_data = flow.gather_data(plan)
    
    # 3. After the user selects sources in the UI, extract them.
    approved_urls = [
        item["url"] for item in search_data["candidates"][:3]
    ] # NOTE: by default, approved urls are first 3 candidate urls.

    # 4. Gather data from the approved sources
    research_data = flow.gather_data(
        plan,
        approved_urls=approved_urls
    )

    # 5. Generate the report and presentation
    output = flow.generate_response(
        requirements,
        plan,
        research_data["sources"],
    )

    create_presentation(
        output["title"],
        output["slides"]
    )

    return render(
        request, 
        "research_output.html", 
        {
            "title":output["title"],
            "executive_summary":output["executive_summary"],
            "report_sections":output["report_sections"],
            "limitations":output["limitations"],
            "references":output["references"]
        }
    )


def home_page(request):
    return render(request, 'home_page.html')


SCOPE_OPTIONS = {
    "fundamental_background",
    "current_developments",
    "applications_use_cases",
    "benefits_opportunities",
    "challenges_limitations",
    "case_studies",
    "future_trends",
    "other",
}
EVIDENCE_OPTIONS = {
    "peer_reviewed_papers",
    "academic_books_reviews",
    "government_reports",
    "industry_reports",
    "reputable_news",
    "case_studies",
    "other",
}
OUTPUT_OPTIONS = {
    "research_report",
    "presentation_slides",
    "executive_summary",
    "reference_list",
}
ROLE_OPTIONS = {
    "academic_researcher": "Academic researcher: conduct evidence-based research and synthesize credible sources.",
    "subject_matter_expert": "Subject matter expert: provide deep, specialized knowledge of the topic.",
    "critical_analyst": "Critical analyst: compare viewpoints, challenge claims, and identify research gaps.",
    "industry_analyst": "Industry analyst: focus on market trends, real-world applications, and industry insights.",
    "science_communicator": "Science communicator: explain complex ideas clearly for easier understanding.",
    "research_assistant": "Research assistant: organize information, summarize findings, and structure the report.",
}
AUDIENCE_OPTIONS = {
    "school_students",
    "undergraduate_students",
    "postgraduate_students",
    "researchers_experts",
    "general_audience",
    "business_professionals",
    "other",
}
ANALYSIS_OPTIONS = {
    "descriptive_overview",
    "balanced_analysis",
    "deep_critical_evaluation",
}
REPORT_WORD_COUNTS = {
    "brief": 500,
    "standard": 1000,
    "detailed": 1500,
    "comprehensive": 2500,
}
SLIDE_COUNTS = {
    "quick_overview": 5,
    "standard_presentation": 8,
    "detailed_presentation": 12,
    "comprehensive_presentation": 15,
}


def _selected_values(post_data, key, allowed_values):
    """ Checks if the selected values are valid or not. """
    values = post_data.getlist(key)
    if any(value not in allowed_values for value in values):
        raise ValueError(f"Invalid selection for {key}.")
    return values


def build_research_requirements(post_data):
    """Convert questionnaire data into the dictionary used by research generation."""

    # fetch data from the form
    topic = post_data.get("topic", "").strip()
    role_option = post_data.get("role", "")
    objective = post_data.get("objective", "").strip()
    audience = post_data.get("audience", "")
    critical_analysis = post_data.get("critical_analysis", "")
    report_length = post_data.get("report_word_count", "")
    slide_length = post_data.get("slide_count", "")

    if not topic or not objective:
        raise ValueError("Topic and objective are required.")
    if role_option in ROLE_OPTIONS:
        role = ROLE_OPTIONS[role_option]
    elif role_option == "other":
        role = post_data.get("role_other", "").strip()
        if not role:
            raise ValueError("Define your custom AI role.")
        if len(role) > 200:
            raise ValueError("Keep your custom AI role to 200 characters or fewer.")
    else:
        raise ValueError("Choose a valid AI role.")
    if audience not in AUDIENCE_OPTIONS or critical_analysis not in ANALYSIS_OPTIONS:
        raise ValueError("Choose a valid audience and analysis depth.")

    scope = _selected_values(post_data, "scope", SCOPE_OPTIONS)
    evidence = _selected_values(post_data, "evidence", EVIDENCE_OPTIONS)
    outputs = _selected_values(post_data, "outputs", OUTPUT_OPTIONS)
    if not scope or not evidence or not outputs:
        raise ValueError("Choose at least one scope, source type, and output.")

    scope_other = post_data.get("scope_other", "").strip()
    audience_other = post_data.get("audience_other", "").strip()
    evidence_other = post_data.get("evidence_other", "").strip()
    if "other" in scope and not scope_other:
        raise ValueError("Describe the additional scope you want to be covered.")
    if audience == "other" and not audience_other:
        raise ValueError("Describe your intended audience.")
    if "other" in evidence and not evidence_other:
        raise ValueError("Specify your preferred source type.")

    if report_length == "custom":
        report_word_count = post_data.get("report_word_count_custom", "").strip()
        if not report_word_count.isdecimal() or not 1 <= int(report_word_count) <= 50000:
            raise ValueError("Enter a custom report length between 1 and 50,000 words.")
        report_word_count = int(report_word_count)
    elif report_length in REPORT_WORD_COUNTS:
        report_word_count = REPORT_WORD_COUNTS[report_length]
    else:
        raise ValueError("Choose a valid report length.")

    if slide_length == "custom":
        slide_count = post_data.get("slide_count_custom", "").strip()
        if not slide_count.isdecimal() or not 1 <= int(slide_count) <= 100:
            raise ValueError("Enter a custom slide count between 1 and 100.")
        slide_count = int(slide_count)
    elif slide_length in SLIDE_COUNTS:
        slide_count = SLIDE_COUNTS[slide_length]
    else:
        raise ValueError("Choose a valid slide count.")

    return {
        "topic": topic,
        "role": role,
        "objective": objective,
        "scope": scope,
        "scope_other": scope_other,
        "audience": audience,
        "audience_other": audience_other,
        "evidence": evidence,
        "evidence_other": evidence_other,
        "critical_analysis": critical_analysis,
        "outputs": outputs,
        "report_word_count": report_word_count,
        "slide_count": slide_count,
    }


@require_http_methods(["GET", "POST"])
def research_questionnaire(request):
    if request.method == "POST":
        try:
            # fetch all values
            requirements = build_research_requirements(request.POST)
        except ValueError as error:
            # display error in case of any invalid values
            return render(
                request,
                "questionnaire.html",
                {"error": str(error)},
                status=400,
            )

        # saving the requirement dictionary in the current django session under a key so that it can be accessed any where.
        request.session["research_requirements"] = requirements
        
        return render(
            request,
            "questionnaire.html",
            {"submitted": True, "requirements": requirements},
        )

    return render(request, "questionnaire.html")

def download_presentation(request):
    # locate the existing powerpoint in the project folder
    ppt_path = Path(__file__).resolve().parents[1] / "presentation.pptx"

    # return 404 response if hte file does not exist
    if not ppt_path.is_file():
        raise Http404("Presentation not found.")

    # send the file as a downloadable attachment.
    return FileResponse(
        open(ppt_path, 'rb'),
        as_attachment=True,
        filename="ResearchFlow_Presentation.pptx"
    )
    # FileResponse sends the file to browser
    # as_attachment=True tells the browser to download it rather than display it.