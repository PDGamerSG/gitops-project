"""Build the completed GitOps case-study report from the supplied Word template."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT.parent / "Case_Study_Project_Report_Template.docx"
DEFAULT_OUTPUT = ROOT / "docs" / "GitOps_Case_Study_Project_Report.docx"
ASSETS = ROOT / "public" / "assets"


def set_font(run, size=None, bold=None, italic=None, name="Times New Roman", color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def set_para(paragraph, size=12, bold=None, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.5):
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line
    fmt.first_line_indent = Inches(0)
    for run in paragraph.runs:
        set_font(run, size=size, bold=bold)
    return paragraph


def set_text(paragraph, text, size=12, bold=None, align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.5):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    run = paragraph.add_run(text)
    set_font(run, size=size, bold=bold)
    set_para(paragraph, size=size, bold=bold, align=align, before=before, after=after, line=line)
    return paragraph


def shade_cell(cell, fill="F2F2F2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=108, bottom=80, end=108):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color="BFBFBF", size="6"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        node = borders.find(tag)
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), size)
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def add_table(doc, headers, rows, widths=None, caption=None):
    if caption:
        caption_paragraph = doc.add_paragraph()
        set_text(caption_paragraph, caption, size=12, bold=True, after=3, line=1.0)
        caption_paragraph.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    set_table_borders(table)
    if widths is None:
        widths = [7.25 / len(headers)] * len(headers)
    for col, width in zip(table.columns, widths):
        col.width = Inches(width)
    header_row = table.rows[0]
    set_repeat_header(header_row)
    for index, value in enumerate(headers):
        cell = header_row.cells[index]
        cell.width = Inches(widths[index])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade_cell(cell, "FFFFFF")
        set_cell_margins(cell)
        set_text(cell.paragraphs[0], str(value), size=12, bold=True, after=2, line=1)
    for row_index, values in enumerate(rows):
        row = table.add_row()
        prevent_row_split(row)
        for index, value in enumerate(values):
            cell = row.cells[index]
            cell.width = Inches(widths[index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            shade_cell(cell, "F2F2F2" if row_index % 2 == 1 else "FFFFFF")
            set_cell_margins(cell)
            set_text(cell.paragraphs[0], str(value), size=12, after=2, line=1)
    doc.add_paragraph()
    return table


def add_heading(doc, text, level=1):
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    run = paragraph.add_run(text)
    size = 16 if level == 1 else 13
    set_font(run, size=size, bold=True)
    # Match the template's built-in heading geometry while keeping the
    # heading attached to the paragraph that follows it.
    set_para(paragraph, size=size, bold=True, before=24 if level == 1 else 10, after=0, line=1.5)
    paragraph.paragraph_format.keep_with_next = True
    return paragraph


def add_body(doc, text, role="body"):
    # The supplied template explicitly requires Times New Roman, 12-point
    # body text and 1.5 line spacing.  Roles remain for call-site clarity,
    # but do not introduce non-template font sizes.
    size = 12
    paragraph = doc.add_paragraph()
    set_text(paragraph, text, size=size, after=0, line=1.5)
    return paragraph


def add_bullets(doc, items):
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        set_text(paragraph, item, size=12, after=0, line=1.5)
        paragraph.paragraph_format.left_indent = Inches(0.25)


def add_label(doc, text, underline=False):
    paragraph = doc.add_paragraph(style="Heading 2")
    run = paragraph.add_run(text)
    set_font(run, size=13, bold=True)
    run.underline = underline
    set_para(paragraph, size=13, bold=True, before=10, after=0, line=1.5)
    paragraph.paragraph_format.keep_with_next = True
    return paragraph


def add_code(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.18)
    paragraph.paragraph_format.right_indent = Inches(0.18)
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph.paragraph_format.line_spacing = 1.0
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "F2F2F2")
    p_pr.append(shd)
    run = paragraph.add_run(text)
    set_font(run, size=10, name="Courier New")
    return paragraph


def add_image(doc, path, caption, width=6.75):
    path = Path(path)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run()
    run.add_picture(str(path), width=Inches(width))
    caption_paragraph = doc.add_paragraph()
    set_text(caption_paragraph, caption, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, line=1.0)
    return paragraph


def add_page_break(doc):
    paragraph = doc.add_paragraph()
    paragraph.add_run().add_break(WD_BREAK.PAGE)


def add_toc_field(doc):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Right-click and update the table of contents in Word."
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])
    set_para(paragraph, size=12, after=0, line=1.5)


def remove_body_after_cover(doc):
    paragraphs = list(doc.paragraphs)
    # Paragraph 22 in the supplied template is the page break that follows
    # the cover.  The builder adds its own break after trimming the template;
    # remove the original break as well so Word does not create an empty page.
    for paragraph in paragraphs[22:]:
        paragraph._element.getparent().remove(paragraph._element)
    for table in list(doc.tables):
        table._element.getparent().remove(table._element)


def configure_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)
    for name, size, before in (("Heading 1", 16, 24), ("Heading 2", 13, 10)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.keep_with_next = True
    for name in ("List Bullet", "List Number"):
        try:
            style = doc.styles[name]
            style.font.name = "Times New Roman"
            style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
            style.font.size = Pt(12)
        except KeyError:
            pass


def set_cover(doc):
    cover = {
        4: ("School of Computer Science Engineering and Information Systems", 14, True),
        5: ("Fall Semester 2026-2027", 14, True),
        7: ("CASE STUDY PROJECT REPORT", 20, True),
        8: ("ON", 14, True),
        9: ("GITOPS-BASED CONTINUOUS DEPLOYMENT USING ARGOCD", 16, True),
        11: ("Submitted by", 14, False),
        12: ("Pallab Das", 14, True),
        13: ("24MIS0212", 14, False),
        15: ("Under the guidance of", 14, False),
        16: ("SCM Course Faculty", 14, True),
        18: ("Submitted in partial fulfilment of the requirements for", 11, False),
        19: ("Software Configuration Management (ISWE403L)", 14, True),
        21: ("October 2026", 14, True),
    }
    for index, (text, size, bold) in cover.items():
        paragraph = doc.paragraphs[index]
        set_text(paragraph, text, size=size, bold=bold, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, line=1.5)


def build(template, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = Document(template)
    configure_styles(doc)
    set_cover(doc)
    remove_body_after_cover(doc)

    add_heading(doc, "ABSTRACT", 1)
    # The cover's trailing break can be pushed onto a second page by Word
    # when the cover fills the page. Start the report with a paragraph-level
    # break instead, which reliably produces one cover page followed by the
    # abstract without an empty interstitial page.
    doc.paragraphs[-1].paragraph_format.page_break_before = True
    add_body(doc, "GitOps applies software configuration management principles to application delivery by making Git the auditable source of desired infrastructure and deployment state. This case study implements a complete pull-based delivery system for a small Node.js Todo service. A source repository is built and tested, an immutable container image is published to a local registry, and a separate configuration repository records the Kubernetes image tag. ArgoCD watches that repository and continuously reconciles a three-replica workload in a local kind cluster. Gitea provides the local Git repositories, while Docker and shell scripts make the workflow reproducible on one Windows machine. The project also includes a public showcase that exposes the workload, Gitea desired state, and ArgoCD application tree as connected views. The verified implementation passed the Node test suite, built and health-checked with Docker Compose, reached Synced and Healthy status in ArgoCD, recovered configuration drift, and supported Git-based rollback. The result demonstrates how a small but complete GitOps loop improves traceability, repeatability, recovery, and presentation of deployment changes.", role="lead")
    add_body(doc, "Keywords: GitOps; ArgoCD; Kubernetes; continuous deployment; software configuration management", role="small")

    add_heading(doc, "TABLE OF CONTENTS", 1)
    add_toc_field(doc)
    add_heading(doc, "LIST OF FIGURES / TABLES / ABBREVIATIONS", 1)
    add_body(doc, "Figures: Figures 1-7 document the architecture, runtime, repository, ArgoCD, and hosted control-plane evidence. Appendix Figures C1-C9 reproduce the supplied setup, CI, Kubernetes, ArgoCD, and runtime diagrams.", role="small")
    add_body(doc, "Tables: Tables 1-9 identify the literature gap, requirements, tools, evaluation criteria, root causes, risks, implementation results, and evaluation evidence.", role="small")
    add_body(doc, "Abbreviations: CI - Continuous Integration; CD - Continuous Delivery; GitOps - Git-based operations; IaC - Infrastructure as Code; YAML - YAML Ain't Markup Language; UI - User Interface; SHA - Secure Hash Algorithm.", role="small")

    add_page_break(doc)
    add_heading(doc, "CHAPTER 1: INTRODUCTION", 1)
    add_heading(doc, "1.1 Background", 2)
    add_body(doc, "Software configuration management requires every change to be identifiable, reviewable, reproducible, and reversible. Traditional deployment workflows often allow a build server or an operator to change a cluster directly. That creates a gap between the configuration recorded in source control and the configuration that is actually running. GitOps closes this gap by treating a Git repository as the desired state and using a controller inside the cluster to pull, apply, and continuously reconcile that state.")
    add_heading(doc, "1.2 Overview of the Case", 2)
    add_body(doc, "The case study is a Todo web service delivered through a local GitOps environment. The application is a zero-dependency Node.js HTTP service with health probes, a Todo API, release metadata, and a browser interface. The source side uses Gitea and a shell-based CI watcher. The delivery side uses a local registry, kind Kubernetes, and ArgoCD. A second Gitea repository stores the Kubernetes manifest. The public Vercel showcase presents the same flow through a Workload tab, a Gitea desired-state tab, and an ArgoCD application-tree tab.")
    add_heading(doc, "1.3 Problem Statement", 2)
    add_body(doc, "The project needed to demonstrate a complete deployment workflow rather than only show an application screen. The main problem was to connect a source change, a tested image, a desired Kubernetes manifest, a reconciled application, and visible evidence while keeping the system runnable on one workstation. The solution also needed to show failure handling, drift recovery, rollback, and the relationship between the source and configuration repositories.")
    add_heading(doc, "1.4 Objectives", 2)
    add_bullets(doc, [
        "Build and test a small Todo application that can run as a container.",
        "Separate application source from Kubernetes desired state in two Git repositories.",
        "Use ArgoCD automated sync, prune, and self-heal to reconcile the cluster.",
        "Verify release, rollback, failed-build, and drift-recovery paths with observable output.",
        "Present the workload, Gitea desired state, and ArgoCD tree as one understandable workflow.",
    ])
    add_heading(doc, "1.5 Scope and Limitations", 2)
    add_body(doc, "The scope includes the Node.js service, Docker image build, local registry, Gitea repositories, kind cluster, ArgoCD Application, release scripts, test evidence, diagrams, and the Vercel showcase. The case is a local demonstration and does not claim production-grade multi-cluster availability, external secret management, or a public Kubernetes service. The hosted page uses browser state and captured local control-plane evidence because a public Vercel deployment cannot directly expose private localhost ports.")
    add_heading(doc, "1.6 Report Organisation", 2)
    add_body(doc, "Chapter 1 introduces the case and objectives. Chapter 2 reviews GitOps and the limitations of a manual workflow. Chapter 3 defines the methodology, requirements, tools, and evaluation criteria. Chapter 4 analyses the scenario and explains the implemented architecture and action plan. Chapter 5 records results, tests, recovery behaviour, and discussion. Chapter 6 concludes the case and lists realistic future enhancements.")

    add_page_break(doc)
    add_heading(doc, "CHAPTER 2: LITERATURE REVIEW / EXISTING SYSTEM", 1)
    add_heading(doc, "2.1 Review of Related Work", 2)
    add_body(doc, "The OpenGitOps principles describe a desired-state, declarative, versioned, immutable, and continuously reconciled operating model [1]. ArgoCD applies this model to Kubernetes by comparing the manifests in a Git source with the live resources in a cluster [2]. Kubernetes provides the declarative resource model and controllers that make the desired state actionable [3]. GitHub Actions and similar CI systems provide the push phase: testing code, building an image, and updating a configuration repository [5]. This project combines those ideas in a small local environment so each handoff can be inspected directly.")
    add_heading(doc, "2.2 Existing System or Current Practice", 2)
    add_body(doc, "A manual workflow typically builds an image, pushes it to a registry, and then applies a deployment file with kubectl. The operator may know which command was run, but the final state is not necessarily represented by a reviewable commit. The source and infrastructure changes can also be mixed together, making it harder to distinguish application code from deployment intent.")
    add_heading(doc, "2.3 Limitations / Research Gap", 2)
    add_table(doc, ["Observed gap", "Impact on delivery"], [
        ["Direct cluster changes", "The running state can diverge from version-controlled configuration."],
        ["One repository for all concerns", "Application and environment changes are harder to review separately."],
        ["Mutable image labels", "A deployment cannot be tied reliably to one source revision."],
        ["Manual recovery", "Rollback and drift correction depend on operator memory and timing."],
        ["Limited evidence", "A demo can show a final screen without proving the steps that produced it."],
    ], widths=[2.35, 4.9], caption="Table 1. Existing workflow gap analysis.")
    add_heading(doc, "2.4 Summary", 2)
    add_body(doc, "The review supports a small pull-based design with Git as the control boundary. The project therefore keeps CI responsible for tests, image creation, and a configuration commit, while ArgoCD remains responsible for reading Git and applying the desired state. This separation is the basis for the proposed solution.")

    add_page_break(doc)
    add_heading(doc, "CHAPTER 3: METHODOLOGY AND REQUIREMENTS", 1)
    add_heading(doc, "3.1 Study Design / Approach", 2)
    add_body(doc, "The project used an implementation case-study approach. First, the application and infrastructure were expressed as files in the repository. Next, the local environment was provisioned and tested. Finally, controlled release, failure, drift, and rollback scenarios were executed and captured. This approach is suitable because the research question is about whether a complete GitOps workflow can be reproduced and observed, rather than about a statistical sample of deployments.")
    add_heading(doc, "3.2 Data Sources and Collection", 2)
    add_body(doc, "Evidence was collected from the project source files, the supplied GitOps reference document, the local command outputs, the Node.js test suite, the Docker Compose health check, the Gitea repository screens, the ArgoCD application tree, and the Todo runtime. The nine diagrams extracted from the supplied document were retained in the project assets and used as supporting architecture evidence. The GitHub repository and Vercel deployment provide the final public source and showcase references.")
    add_heading(doc, "3.3 Functional Requirements", 2)
    add_table(doc, ["ID", "Requirement", "Evidence"], [
        ["FR1", "Create and operate the Todo service with health checks and Todo actions.", "Node tests, runtime screen, /healthz and /api/todos."],
        ["FR2", "Build an image only after the test suite passes.", "Two-stage Dockerfile and passing node --test output."],
        ["FR3", "Record the desired image in a separate Git configuration repository.", "config-repo/manifest.yml and Gitea desired-state view."],
        ["FR4", "Synchronize and self-heal the Kubernetes workload.", "ArgoCD Application with automated, prune, and selfHeal."],
        ["FR5", "Show the change in the workload, Gitea, and ArgoCD views.", "Live control-plane console and browser interaction check."],
    ], widths=[0.55, 3.8, 2.9], caption="Table 2. Functional requirements.")
    add_heading(doc, "3.4 Non-functional Requirements", 2)
    add_table(doc, ["Quality", "Target in this case", "Implementation"], [
        ["Repeatability", "One workstation can recreate the environment.", "gitops.cmd setup, Docker Compose, kind, and scripts."],
        ["Traceability", "Every deployment maps to a Git revision.", "Commit-addressed image tags and config history."],
        ["Recovery", "Drift and rollback are observable and reversible.", "ArgoCD self-heal and Git revert workflow."],
        ["Usability", "A reviewer can follow the workflow without hidden steps.", "Tabbed showcase, screenshots, diagrams, and README."],
        ["Safety", "Broken application code does not ship.", "Tests run before the runtime image is produced."],
    ], widths=[1.2, 2.65, 3.4], caption="Table 3. Non-functional requirements.")
    add_heading(doc, "3.5 Tools and Technologies", 2)
    add_table(doc, ["Tool / technology", "Version or form", "Purpose"], [
        ["Node.js", "22 Alpine image", "Todo service and unit tests."],
        ["Docker", "Dockerfile and Compose", "Tested image build and standalone runtime."],
        ["Kubernetes", "kind cluster gitops", "Local three-node deployment target."],
        ["ArgoCD", "Local controller", "Pull-based sync, health, prune, and self-heal."],
        ["Gitea", "Local Git service", "Source and desired-state repositories."],
        ["Registry", "registry:2 at localhost:5001", "Local immutable image storage."],
        ["GitHub / Vercel", "Public repository and showcase", "Source publication and hosted presentation."],
    ], widths=[1.65, 2.05, 3.55], caption="Table 4. Tools and technologies.")
    add_heading(doc, "3.6 Evaluation Criteria", 2)
    add_table(doc, ["Criterion", "Pass condition"], [
        ["Application correctness", "All Node.js tests pass and health check returns success."],
        ["Pipeline correctness", "A release changes the image tag and produces a config commit."],
        ["Reconciliation", "ArgoCD reaches Synced / Healthy with three ready replicas."],
        ["Drift recovery", "Manual cluster drift is restored by ArgoCD without editing the cluster back."],
        ["Rollback", "A Git revert returns the desired image to the previous revision."],
        ["Communication", "Screenshots and the live console explain the same state consistently."],
    ], widths=[2.0, 5.25], caption="Table 5. Evaluation criteria.")

    add_page_break(doc)
    add_heading(doc, "CHAPTER 4: CASE STUDY ANALYSIS AND PROPOSED SOLUTION", 1)
    add_heading(doc, "4.1 Case Scenario and Assumptions", 2)
    add_body(doc, "The scenario is a small development team releasing a Todo service from a Windows workstation. The team needs a local environment that behaves like a pull-based production delivery system: code changes are tested, an image is identified by its revision, desired state is committed separately, and a controller converges the cluster. The scenario assumes Docker Desktop, Git for Windows, kind, kubectl, and Python are available. The local Gitea credentials are demo credentials and are not intended for production use.")
    add_heading(doc, "4.2 Root-Cause / Gap Analysis", 2)
    add_table(doc, ["Problem", "Root cause", "GitOps response"], [
        ["Unknown running revision", "Image and deployment state are not linked to one commit.", "Use an immutable commit SHA tag in the manifest."],
        ["Configuration drift", "Operators can change live resources outside version control.", "Enable ArgoCD automated sync and self-heal."],
        ["Difficult rollback", "The last known good configuration is not easy to identify.", "Use a Git revert on the desired-state repository."],
        ["Unclear evidence", "Final UI state hides intermediate handoffs.", "Expose CI, Gitea, ArgoCD, and runtime evidence together."],
    ], widths=[1.8, 2.65, 2.8], caption="Table 6. Root-cause and gap analysis.")
    add_heading(doc, "4.3 Proposed Solution", 2)
    add_body(doc, "The proposed solution has two repositories and one reconciliation boundary. The source repository contains server.js, version.json, the Dockerfile, and tests. The configuration repository contains manifest.yml. CI builds the application image, pushes it to the registry, changes only the image tag in manifest.yml, and pushes that commit. ArgoCD polls the configuration repository, applies the Deployment and Service, reports health, and restores drift. The public showcase mirrors the same relationships in a readable interface.")
    add_heading(doc, "4.4 System Design / Workflow", 2)
    add_body(doc, "The delivery loop is intentionally pull-based. The CI side does not need cluster credentials; it writes a desired-state commit. ArgoCD performs the pull and applies the desired resources inside the cluster.")
    add_image(doc, ASSETS / "diagrams" / "diagram-02.png", "Figure 1. Declarative GitOps deployment loop extracted from the project reference document.", width=6.9)
    add_body(doc, "The local implementation contains a kind cluster named gitops, a local registry on port 5001, Gitea on port 3300, ArgoCD on port 8080, and the Todo service on port 8081. The Kubernetes Application watches the argo-deployment repository and enables automated sync, prune, and self-heal.")
    add_heading(doc, "4.5 Implementation / Action Plan", 2)
    add_label(doc, "Step 1: Initialize the project")
    add_body(doc, "The repository was organised into app, config-repo, infra, scripts, and public assets. The setup command creates the registry, cluster, Gitea repositories, ArgoCD installation, initial image, and Application.")
    add_code(doc, ".\\gitops.cmd setup\n.\\gitops.cmd status")
    add_label(doc, "Step 2: Build and test the application")
    add_body(doc, "The Dockerfile uses a test stage before the runtime stage. The test stage runs the Node.js test suite, so a broken test fails the image build before the runtime layer can be produced.")
    add_code(doc, "cd app\nnpm test\ndocker compose up --build")
    add_image(doc, ASSETS / "todo-runtime.png", "Figure 2. Todo runtime evidence showing release metadata, image commit, pod, node, and health.", width=6.55)
    add_label(doc, "Step 3: Commit desired Kubernetes state")
    add_body(doc, "The configuration repository contains a Deployment with three replicas and a NodePort Service. Readiness and liveness probes call /healthz. The only value changed by the CI flow is the image tag, which keeps deployment intent easy to review.")
    add_code(doc, "git clone http://localhost:3300/gitops/argo-deployment.git\n# update image: localhost:5001/todo-app:<commit-sha>\ngit add manifest.yml\ngit commit -m \"Update image tag\"\ngit push origin main")
    add_image(doc, ASSETS / "gitea-ops-repository.png", "Figure 3. Gitea desired-state repository with the manifest and CI Bot commit.", width=6.55)
    add_label(doc, "Step 4: Reconcile the cluster")
    add_body(doc, "ArgoCD watches the desired-state repository and applies the manifest to the default namespace. Automated sync, prune, and self-heal are enabled in infra/argocd-application.yaml.")
    add_code(doc, "kubectl get pods\nkubectl get svc\n# ArgoCD UI\nhttp://localhost:8080/applications/argocd/todo-app?view=tree")
    add_image(doc, ASSETS / "argocd-application.png", "Figure 4. ArgoCD application tree showing the Todo Deployment, Service, ReplicaSet, and ready pods.", width=6.55)
    add_label(doc, "Step 5: Present the complete workflow")
    add_body(doc, "The local showcase is served with the same public assets used by the Vercel deployment. The Control plane tab contains connected Workload, Gitea desired-state, and ArgoCD application-tree screens. Browser state is shared across tabs so a Todo change can be shown moving through the GitOps stages.")
    add_code(doc, ".\\gitops.cmd showcase\n# open http://localhost:4173")
    showcase = ASSETS / "live-control-plane.png"
    if showcase.exists():
        add_image(doc, showcase, "Figure 5. Local showcase control-plane console with linked Workload, Gitea, and ArgoCD views.", width=6.6)
    add_heading(doc, "4.6 Security, Ethics, and Risk Considerations", 2)
    add_table(doc, ["Risk", "Control used in the project"], [
        ["Demo credentials exposed locally", "Credentials are documented as local demo values and are not production secrets."],
        ["Cluster credentials in CI", "CI writes Git only; ArgoCD holds the pull-side cluster access."],
        ["Mutable deployment state", "The manifest records a commit-addressed image tag and ArgoCD self-heals drift."],
        ["Supply-chain trust", "The Docker test stage runs before the runtime image is created; production signing is future work."],
        ["Hosted evidence confusion", "The showcase labels captured localhost screens and separates them from the live browser projection."],
    ], widths=[2.05, 5.2], caption="Table 7. Security, ethics, and risk controls.")

    add_page_break(doc)
    add_heading(doc, "CHAPTER 5: RESULTS AND DISCUSSION", 1)
    add_heading(doc, "5.1 Implementation or Study Results", 2)
    add_body(doc, "The implementation was exercised locally and the resulting evidence was published with the project. The Node.js tests passed, the standalone container health check passed, and the local ArgoCD application reached Synced / Healthy with three replicas. The release, rollback, failure, and drift scenarios are represented by scripts and captured screens.")
    add_table(doc, ["Test or observation", "Observed result", "Status"], [
        ["Node.js test suite", "4 tests passed; health, info, Todo actions, and validation covered.", "Pass"],
        ["Docker Compose", "Build completed and the /healthz check returned success.", "Pass"],
        ["ArgoCD application", "Synced / Healthy with three running Todo pods.", "Pass"],
        ["Release path", "Commit, test/build, registry push, config commit, and ArgoCD rollout completed.", "Pass"],
        ["Drift demonstration", "Replica and Service drift were restored automatically by ArgoCD.", "Pass"],
        ["Rollback", "A Git revert returned the desired image to the previous revision.", "Pass"],
        ["Hosted showcase", "Vercel deployment served the live control-plane asset and page successfully.", "Pass"],
    ], widths=[1.8, 4.55, 0.9], caption="Table 8. Implementation and test results.")
    add_image(doc, ASSETS / "gitea-source-repository.png", "Figure 6. Gitea source repository containing the application, tests, Dockerfile, and release metadata.", width=6.55)
    add_heading(doc, "5.2 Evaluation", 2)
    add_body(doc, "The functional criteria were met because the application, image build, desired state, reconciliation, and presentation are all connected. The three-replica Deployment provides a visible rolling-update target. The commit-addressed image and Gitea history provide traceability. The ArgoCD tree provides a direct view of the resources that were created from Git. The workflow simulator and live control-plane console make the same transitions understandable to a reviewer who does not have the local cluster open.")
    add_table(doc, ["Evaluation area", "Evidence used", "Finding"], [
        ["Correctness", "npm test and /healthz", "The service behaves as expected before deployment."],
        ["Traceability", "Gitea commit list and manifest image tag", "Desired state identifies the release revision."],
        ["Reconciliation", "ArgoCD tree and status badges", "The cluster converges to Git and reports health."],
        ["Recovery", "drift-demo and rollback scripts", "The system can restore or reverse state through Git."],
        ["Communication", "Showcase tabs and screenshots", "The workflow is visible without hiding the important handoffs."],
    ], widths=[1.65, 2.8, 2.8], caption="Table 9. Evaluation evidence.")
    add_heading(doc, "5.3 Discussion", 2)
    add_body(doc, "The main benefit is the separation between the push phase and the pull phase. CI does not need to run kubectl against the cluster, and the cluster does not need to trust every build process with direct write access. The configuration repository becomes the reviewable boundary for deployment intent. ArgoCD also turns drift from a silent operational problem into an observable state that can be repaired. The design is intentionally small, but the same boundaries can be extended to multiple environments and clusters.")
    add_heading(doc, "5.4 Limitations", 2)
    add_body(doc, "The demonstration uses one local kind cluster and a local registry rather than a highly available production platform. The browser control-plane views are projections of shared showcase state; the public Vercel page cannot directly connect to private localhost Gitea and ArgoCD ports. The project does not yet include image signing, a managed secret store, policy enforcement, progressive delivery, or external monitoring. These limitations are acceptable for the case study but should be addressed before production adoption.")
    add_image(doc, ASSETS / "diagrams" / "diagram-08.png", "Figure 7. Synced ArgoCD application evidence extracted from the project reference document.", width=6.55)

    add_page_break(doc)
    add_heading(doc, "CHAPTER 6: CONCLUSION AND FUTURE WORK", 1)
    add_heading(doc, "6.1 Conclusion", 2)
    add_body(doc, "This case study implemented and documented a complete GitOps delivery loop for a Node.js Todo application. The source repository, tested container image, configuration repository, local registry, kind cluster, ArgoCD controller, and public showcase work together as one configuration-managed system. The evidence confirms that changes can be tested, committed as desired state, reconciled into three running pods, shown in the Gitea and ArgoCD views, recovered from drift, and reversed through Git. The project therefore meets the main objectives of demonstrating traceability, repeatability, reconciliation, and observable recovery in a local Software Configuration Management environment.")
    add_heading(doc, "6.2 Future Enhancements", 2)
    add_bullets(doc, [
        "Enable the GitHub Actions workflow after authorising the repository workflow scope and use a managed image registry.",
        "Add image signing, SBOM generation, vulnerability scanning, and admission policies.",
        "Move credentials to a secret manager and replace demo passwords with short-lived tokens.",
        "Add staging and production overlays with promotion gates and progressive delivery.",
        "Connect the hosted showcase to a secured remote telemetry API instead of browser-only state.",
        "Add Prometheus metrics, alerts, and deployment-frequency / lead-time measurements.",
    ])

    add_page_break(doc)
    add_heading(doc, "REFERENCES", 1)
    references = [
        "[1] OpenGitOps, \"OpenGitOps Principles,\" OpenGitOps, https://opengitops.dev/, accessed October 2026.",
        "[2] Argo Project, \"Argo CD Documentation,\" https://argo-cd.readthedocs.io/, accessed October 2026.",
        "[3] Kubernetes Authors, \"Kubernetes Documentation,\" https://kubernetes.io/docs/, accessed October 2026.",
        "[4] Docker, \"Docker Documentation,\" https://docs.docker.com/, accessed October 2026.",
        "[5] GitHub, \"GitHub Actions Documentation,\" https://docs.github.com/actions, accessed October 2026.",
        "[6] Gitea, \"Gitea Documentation,\" https://docs.gitea.com/, accessed October 2026.",
        "[7] Kubernetes SIGs, \"kind - Kubernetes IN Docker,\" https://kind.sigs.k8s.io/, accessed October 2026.",
        "[8] P. Das, \"GitOps continuous deployment with ArgoCD,\" project repository, https://github.com/PDGamerSG/gitops-project, October 2026.",
        "[9] P. Das, \"GitOps project reference document,\" supplied ODT document, Research Paper folder, October 2026.",
    ]
    for reference in references:
        add_body(doc, reference, role="reference")

    add_page_break(doc)
    add_heading(doc, "APPENDICES", 1)
    add_heading(doc, "Appendix A: Project Structure", 2)
    add_code(doc, "gitops-project/\n|-- app/                         Node.js workload, tests, Dockerfile\n|-- config-repo/                 Kubernetes desired state\n|-- infra/                       kind and ArgoCD manifests\n|-- scripts/                     setup, release, drift, rollback, showcase\n|-- public/                      Vercel showcase and evidence assets\n|-- docker-compose.yml           standalone runtime\n`-- gitops.cmd                   Windows command entry point")
    add_heading(doc, "Appendix B: Demonstration Commands", 2)
    add_code(doc, ".\\gitops.cmd setup\n.\\gitops.cmd ci-watch\n.\\gitops.cmd release\n.\\gitops.cmd drift-demo\n.\\gitops.cmd rollback\n.\\gitops.cmd showcase")
    add_body(doc, "The local showcase is available at http://localhost:4173. The local Todo workload is exposed at http://localhost:8081 after setup, ArgoCD at http://localhost:8080, Gitea at http://localhost:3300, and the registry at http://localhost:5001.", role="small")

    add_page_break(doc)
    add_heading(doc, "Appendix C: Reference Diagrams and Architecture Evidence", 2)
    add_body(doc, "The following figures are reproduced from the supplied research reference material and retained with the report so the architecture, CI handoff, cluster evidence, and ArgoCD evidence remain available in one submission.", role="small")
    reference_diagrams = [
        ("diagram-01.png", "Appendix Figure C1. Initial local GitOps setup sequence."),
        ("diagram-02.png", "Appendix Figure C2. Declarative GitOps deployment loop."),
        ("diagram-03.png", "Appendix Figure C3. CI workflow definition."),
        ("diagram-04.png", "Appendix Figure C4. CI repository and image update commands."),
        ("diagram-05.png", "Appendix Figure C5. Kubernetes pod health evidence."),
        ("diagram-06.png", "Appendix Figure C6. ArgoCD application tree evidence."),
        ("diagram-07.png", "Appendix Figure C7. Kubernetes and ArgoCD service evidence."),
        ("diagram-08.png", "Appendix Figure C8. Synced ArgoCD application evidence."),
        ("diagram-09.png", "Appendix Figure C9. Runtime log evidence."),
    ]
    for filename, caption in reference_diagrams:
        add_image(doc, ASSETS / "diagrams" / filename, caption, width=6.65)

    # Keep the template footer and page geometry, but ensure all generated paragraphs use the report font.
    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        for container in (section.header, section.footer):
            for paragraph in container.paragraphs:
                for run in paragraph.runs:
                    set_font(run, size=10)

    doc.core_properties.title = "GitOps-Based Continuous Deployment Using ArgoCD"
    doc.core_properties.subject = "Software Configuration Management case study project report"
    doc.core_properties.author = "Pallab Das"
    doc.core_properties.keywords = "GitOps, ArgoCD, Kubernetes, SCM, continuous deployment"
    doc.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.template, args.output)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
