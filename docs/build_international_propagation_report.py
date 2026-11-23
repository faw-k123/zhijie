from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


OUT = Path(__file__).with_name("智解国音国际传播功能建设汇报.docx")


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=140, bottom=80, end=140):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_border(cell, color="D9D9D9", size="6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def set_run_font(run, east="Microsoft YaHei", latin="Aptos", size=None, bold=None, color="000000"):
    run.font.name = latin
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), east)
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), latin)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), latin)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)
    set_run_font(run, size=8, color="666666")


def add_para(doc, text="", style=None, bold_lead=None, align=None, keep=False):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if bold_lead and text.startswith(bold_lead):
        r1 = p.add_run(bold_lead)
        set_run_font(r1, size=10.5, bold=True)
        r2 = p.add_run(text[len(bold_lead):])
        set_run_font(r2, size=10.5)
    else:
        r = p.add_run(text)
        set_run_font(r, size=10.5)
    p.paragraph_format.line_spacing = 1.45
    p.paragraph_format.space_after = Pt(7)
    p.paragraph_format.keep_together = keep
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph()
    r = p.add_run(f"•  {text}")
    set_run_font(r, size=10.2)
    p.paragraph_format.left_indent = Cm(0.7 + level * 0.5)
    p.paragraph_format.first_line_indent = Cm(-0.25)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(4)
    return p


def add_number(doc, text):
    p = doc.add_paragraph(style="List Number")
    r = p.add_run(text)
    set_run_font(r, size=10.2)
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.3)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(4)
    return p


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, header in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_shading(cell, "1F4E78")
        set_cell_margins(cell)
        set_cell_border(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if widths:
            cell.width = Cm(widths[i])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(header)
        set_run_font(r, size=9.2, bold=True, color="FFFFFF")
    for row_i, values in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(values):
            cell = cells[i]
            set_cell_margins(cell)
            set_cell_border(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if widths:
                cell.width = Cm(widths[i])
            if row_i % 2 == 1:
                set_cell_shading(cell, "F3F7FA")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.25
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(value))
            set_run_font(r, size=9.0)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.4)
section.bottom_margin = Cm(2.2)
section.left_margin = Cm(2.55)
section.right_margin = Cm(2.55)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "Aptos"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
normal.font.size = Pt(10.5)
normal.font.color.rgb = RGBColor(0, 0, 0)

title_style = styles["Title"]
title_style.font.name = "Aptos Display"
title_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
title_style.font.size = Pt(24)
title_style.font.bold = True
title_style.font.color.rgb = RGBColor(0, 0, 0)
title_style.paragraph_format.space_after = Pt(18)
title_ppr = title_style._element.get_or_add_pPr()
title_border = title_ppr.find(qn("w:pBdr"))
if title_border is not None:
    title_ppr.remove(title_border)

for style_name, size, before, after in (("Heading 1", 16, 18, 9), ("Heading 2", 12.5, 13, 6), ("Heading 3", 11, 9, 4)):
    st = styles[style_name]
    st.font.name = "Aptos"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True

footer = section.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.LEFT
fr = fp.add_run("智解国音国际传播功能建设汇报")
set_run_font(fr, size=8, color="666666")
add_page_number(footer.add_paragraph())

# Cover
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(75)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("智解国音")
set_run_font(r, size=13, bold=True, color="1F4E78")

p = doc.add_paragraph(style="Title")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_pr = p._p.get_or_add_pPr()
p_border = p_pr.find(qn("w:pBdr"))
if p_border is not None:
    p_pr.remove(p_border)
r = p.add_run("国际传播功能建设汇报")
set_run_font(r, east="Microsoft YaHei", latin="Aptos Display", size=24, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(26)
r = p.add_run("教师修改意见落实情况与系统实现说明")
set_run_font(r, size=13, color="444444")

add_para(
    doc,
    "本报告汇报国际传播功能从研究过程页面向成果展示页面的调整情况，重点说明全球传播效果、海外案例库、区域传播方案以及单曲情感分析中的海外传播栏目。报告同时交代数据口径、案例证据、接受机制、匹配规则和当前研究边界。",
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(95)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("汇报日期  2026年11月")
set_run_font(r, size=10.5, color="555555")

doc.add_page_break()

doc.add_heading("一 项目调整结论", level=1)
add_para(
    doc,
    "本阶段已经完成国际传播用户端的结构收口，并将主要成果集中到三个页面：全球传播效果、海外案例库和区域传播方案。研究洞察、专项研究成果、六国实测工作台等过程性页面不再出现在普通用户导航中。单曲情感分析详情页保留原有的海外传播栏目，并补充候选曲传播画像、影响因素参考、案例匹配和区域方案。",
)
add_para(
    doc,
    "系统目前可以回答四类问题：案例涉及哪些国家，哪些因素在现有样本中占比较高，外国受众为什么接受中国传统音乐，以及不同国家应当采用怎样的主题、形式和文化适配方式。所有结果都尽量回到具体案例、评分和来源，无法确认的数据保持未知。",
)

add_table(
    doc,
    ["成果模块", "主要回答的问题", "当前实现"],
    [
        ["全球传播效果", "案例涉及哪些国家，影响因素占比如何", "按严格案例统计国家分布和10项因素的样本内编码占比"],
        ["海外案例库", "有哪些外国人演奏中国传统音乐的可靠案例", "只展示已审批严格案例，支持检索、筛选和详情追溯"],
        ["区域传播方案", "不同国家如何选择曲目、主题和传播形式", "提供日本、泰国、英国、美国、阿联酋和巴西六国方案"],
        ["单曲海外传播", "当前歌曲可以参考哪些机制、案例和国别方案", "区分直接关联、同类候选参考、机制匹配和总体参考"],
    ],
    widths=[3.2, 6.0, 7.0],
)

doc.add_heading("二 教师意见的落实思路", level=1)
add_para(
    doc,
    "教师意见要求研究不能停留在采集案例和制作页面，而要形成可解释的国际传播结果。系统因此把案例、外国受众反馈、接受机制、候选音乐和区域方案连接起来，形成从证据到结果的连续链条。",
)
for text in [
    "案例层回答谁在海外演奏中国传统音乐，以及案例是否满足严格准入条件。",
    "受众层记录外国受众的原始反馈、反馈语境、情感倾向和证据限制。",
    "机制层把反馈编码为情绪共鸣、独特音色、熟悉性桥梁等接受原因。",
    "音乐层根据案例机制选择首批20首候选音乐，并记录入选理由、时代主题、传播形式和风险。",
    "区域层把候选音乐与六个国家的文化背景、宗教注意事项、目标受众和传播平台连接起来。",
]:
    add_number(doc, text)

doc.add_heading("三 用户端页面结构调整", level=1)
doc.add_heading("三点一 国际传播导航", level=2)
add_para(
    doc,
    "国际传播主导航现在只保留全球传播效果、海外案例库和区域传播方案三个结果入口。研究洞察、专项研究成果和六国实测工作台已经从普通用户导航中移除。旧地址仍保留重定向，以免历史链接失效，但用户不会再进入过程性工作台。",
)

doc.add_heading("三点二 情感分析中的海外传播", level=2)
add_para(
    doc,
    "海外传播没有被新增为顶部导航页面，而是保留在单曲情感分析详情页底部。用户选择一首歌曲后，可以在同一页面查看该曲的候选状态、传播画像、参考因素、案例和区域方案。这样既保持原有操作路径，也避免国际传播模块继续增加页面数量。",
)

doc.add_heading("四 全球传播效果", level=1)
doc.add_heading("四点一 国家与区域分布", level=2)
add_para(
    doc,
    "全球传播效果页只统计已经审批通过的严格外国个人案例。扩展跨文化案例、待核实案例和未审批记录不进入国家占比。页面展示严格案例数、覆盖国家数、涉及乐器种类、各国案例数以及各国在当前严格样本中的占比。",
)
add_para(
    doc,
    "国家占比反映当前案例库的样本构成，不代表某个国家的真实市场份额，也不能直接解释为国家偏好。页面已经增加相应口径说明，避免把样本分布误读为总体传播效果。",
)

doc.add_heading("四点二 传播影响因素占比", level=2)
add_para(
    doc,
    "系统汇总严格案例的10项传播影响因素评分，并把各因素平均分归一化为样本内编码占比。页面同时显示平均分、有效案例数量和占比。该结果用于比较当前样本中哪些因素表现更突出，不作为因果贡献率。",
)
add_table(
    doc,
    ["展示内容", "计算或展示口径", "解释限制"],
    [
        ["因素平均分", "只计算有证据的有效评分", "未知值不按0分处理"],
        ["因素占比", "各因素平均分在全部有效因素分值中的相对比例", "是描述性构成，不是因果贡献"],
        ["有效案例数", "每项因素实际具有有效评分的严格案例数", "不同因素有效样本可能不同"],
    ],
    widths=[3.4, 7.3, 5.5],
)

doc.add_heading("五 海外案例库", level=1)
doc.add_heading("五点一 严格案例范围", level=2)
add_para(
    doc,
    "案例库默认只展示已审批的严格海外个人案例。严格案例要求具名外国个人、明确的中国音乐对象、实际演奏行为、海外或跨国传播场景，并至少有两条能够共同支持身份、乐器和演奏事实的可追溯来源。",
)
add_para(
    doc,
    "案例库支持关键词、国家、乐器和证据等级筛选。列表展示演奏者、国家、乐器、摘要、编码均分和来源数量。用户点击案例后进入完整详情。",
)

doc.add_heading("五点二 案例详情", level=2)
add_para(doc, "每个案例详情页已经形成以下结果结构：")
for text in [
    "案例摘要和背景，包括国家、区域、乐器、音乐类型、活动时间、地点、传播渠道、目标受众、学习动机和改编方式。",
    "10项影响因素评分，包括分数、评分证据、来源编号、缺失原因和审批状态。",
    "案例信息和来源索引，来源可以追溯到标题、发布者、可靠性、原始链接及其支持的具体事实。",
    "外国受众反馈证据，逐条展示原始摘录、语言、情感倾向、受众语境、证据等级和限制。",
    "外国受众接受原因，只突出已经获得强证据或部分证据的接受机制。",
    "传播结果类型，区分接受认可、互动参与、学习或行动转化以及机构化延续。",
]:
    add_bullet(doc, text)

doc.add_heading("六 外国受众反馈和接受机制", level=1)
doc.add_heading("六点一 反馈证据", level=2)
add_para(
    doc,
    "系统没有把播放量或泛化的好评直接等同于外国受众接受。反馈记录分别保存反馈类型、证据等级、语言、情感倾向、受众语境、原文摘录、摘要、限制和来源链接。例如，受众明确表示因某位演奏者开始学习二胡时，该反馈被归为学习转化证据。",
)

doc.add_heading("六点二 九类接受机制", level=2)
add_table(
    doc,
    ["编码", "机制", "含义"],
    [
        ["M1", "情绪共鸣", "受众因情感表达、氛围或个人体验产生认同"],
        ["M2", "独特音色", "中国传统乐器音色形成注意力入口"],
        ["M3", "熟悉性桥梁", "影视、流行、游戏或当地音乐元素降低理解门槛"],
        ["M4", "文化叙事", "曲目背景、人物、历史或意象帮助理解"],
        ["M5", "跨文化转译", "通过编配、合作或表达方式连接不同音乐文化"],
        ["M6", "演奏者可信度", "演奏能力、长期学习和个人经历增强信任"],
        ["M7", "视觉与表演性", "技巧、动作、舞台和影像增强观看体验"],
        ["M8", "数字平台适配", "短视频、平台传播和多语种内容扩大接触"],
        ["M9", "教育与参与转化", "受众进一步学习、参与、收藏或持续关注"],
    ],
    widths=[1.5, 4.1, 10.6],
)
add_para(
    doc,
    "每个案例的机制状态分为强证据、部分证据和未见证据。机制编码说明现有证据支持的接受路径，不从国籍、姓名或宗教背景直接推断偏好。",
)

doc.add_heading("七 首批20首候选音乐", level=1)
add_para(
    doc,
    "首批20首候选音乐已经完成选择，并保存候选层级、主要接受机制、时代主题、国际呈现形式、入选理由、主要风险和首轮验证方向。候选曲包括器乐、民歌、戏曲和说唱等类型。",
)
add_para(
    doc,
    "目前候选选择已经完成，但六国受众实验尚未产生正式评分。因此系统可以展示为什么选择某首音乐、它可能通过哪些机制被接受，以及适合怎样的主题和形式；不能把尚未采集的实测数据写成正式总分。",
)
add_table(
    doc,
    ["结果字段", "页面作用"],
    [
        ["候选层级", "说明曲目在首批候选中的优先程度"],
        ["主要机制", "连接案例编码得到的接受原因"],
        ["时代主题", "把传统音乐与当代议题连接起来"],
        ["国际呈现形式", "给出短视频、音乐会、合奏或多媒体等形式"],
        ["入选理由", "说明为何该曲具有国际传播潜力"],
        ["主要风险", "提示误读、刻板化、宗教或文化语境风险"],
    ],
    widths=[4.2, 11.9],
)

doc.add_heading("八 六国区域传播方案", level=1)
add_para(
    doc,
    "区域传播方案覆盖日本、泰国、英国、美国、阿联酋和巴西。每个国家均设置优先音乐、次优音乐、需要背景解释的音乐、主要进入机制、主题框架、改编设计、语言中介方式以及宗教和文化注意事项。",
)
add_table(
    doc,
    ["国家", "主要主题方向", "适配重点"],
    [
        ["日本", "青年交流 自然审美 女性故事", "影视化叙事 短字幕 保留传统乐器音色"],
        ["泰国", "水域文明 自然生态 社区节庆", "与当地弦乐管乐合作 增加参与性副歌"],
        ["英国", "文明对话 实验创作 女性表达", "导赏音乐会 室内乐 声音艺术合作"],
        ["美国", "多元社区 青年成长 社会连接", "人物故事 技巧短片 校园与社区工作坊"],
        ["阿联酋", "丝绸之路 自然 家庭友谊", "纯器乐 家族友好 避免不当历史同源叙述"],
        ["巴西", "社区节庆 土地记忆 迁徙表达", "节奏合作 共同演唱 保留核心旋律和乐器"],
    ],
    widths=[2.4, 6.2, 7.5],
)

doc.add_heading("九 单曲情感分析中的海外传播", level=1)
doc.add_heading("九点一 页面定位", level=2)
add_para(
    doc,
    "海外传播栏目位于单曲情感分析详情页底部。它不是新的顶部页面，而是把当前歌曲与候选音乐、严格案例和六国方案连接起来。页面目前包含曲目关联状态、传播画像、因素参考、案例匹配、区域方案和结果摘要。",
)

doc.add_heading("九点二 候选曲和普通曲目的不同处理", level=2)
add_para(
    doc,
    "如果当前歌曲属于首批20首候选曲，页面直接展示该曲的候选层级、入选理由、时代主题、国际形式、风险和8项潜力指标。若当前歌曲不属于首批20首，例如东北人都是活雷锋，页面不会再错误显示为已选曲，而是展示民歌类候选曲传播画像。",
)
add_para(
    doc,
    "同类候选参考会列出同类别候选曲及其已经审批的机制、主题和传播形式，并明确说明这些内容不是当前歌曲的六国实测结论。这样可以让页面产生可阅读的研究结果，同时避免伪造单曲评分。",
)

doc.add_heading("九点三 案例匹配", level=2)
add_para(
    doc,
    "案例匹配采用分层规则。已登记的直接关联案例优先展示；没有直接案例时，系统根据同类乐器和接受机制从严格案例库中寻找参考案例；无法形成机制匹配时，才展示案例库总体参考。",
)
add_table(
    doc,
    ["案例层级", "匹配依据", "页面表述"],
    [
        ["直接关联案例", "候选音乐记录中明确登记的案例编号", "可以作为该候选音乐的直接关联证据"],
        ["机制匹配案例", "同类乐器 强机制重合 部分机制重合", "属于机制参考 不冒充本曲实际演奏事实"],
        ["总体参考案例", "严格案例库中证据较完整的案例", "只说明案例库整体经验"],
    ],
    widths=[3.3, 6.1, 7.1],
)
add_para(
    doc,
    "每个机制匹配案例显示匹配分和匹配原因。匹配原因使用可读文字呈现，例如同类乐器二胡、强机制重合情绪共鸣和跨文化转译、部分机制重合文化叙事。用户可以继续点入案例详情查看受众反馈和来源。",
)

doc.add_heading("九点四 区域方案", level=2)
add_para(
    doc,
    "如果区域矩阵明确包含当前候选音乐，页面展示该曲对应的国别方案。如果没有直接适配记录，则展示六国总体方案框架，并明确标注为总体参考，不作为当前歌曲已经验证的国家结论。",
)

doc.add_heading("十 数据口径和研究边界", level=1)
add_para(
    doc,
    "系统已经区分直接事实、编码结果、机制匹配和总体参考。这个区分关系到研究结论是否可靠，也是本次功能调整的核心。",
)
add_table(
    doc,
    ["结果类型", "可以说明什么", "不能说明什么"],
    [
        ["案例事实", "某位外国演奏者确实演奏或传播了中国音乐", "不能代表外国受众总体偏好"],
        ["受众反馈", "具体受众表达了认可 参与或学习转化", "不能从目的抽样推断总体比例"],
        ["机制编码", "现有证据支持哪些接受路径", "不能直接证明因果关系"],
        ["因素占比", "当前严格样本的编码分值构成", "不能解释为市场贡献率"],
        ["机制匹配", "某案例与候选曲共享乐器或接受机制", "不能冒充该案例演奏过当前歌曲"],
        ["六国方案", "给出经审核的文化适配框架", "不能代替尚未完成的真实受众实验"],
    ],
    widths=[3.0, 6.5, 7.0],
)

doc.add_heading("十一 技术实现和验证", level=1)
add_para(
    doc,
    "后端案例详情接口增加了受众反馈、接受机制、机制置信度、传播结果状态和结果标签。单曲海外传播接口增加了候选曲元数据、同类候选参考、机制匹配案例、匹配分、匹配原因、严格案例因素占比和六国总体方案参考。前端根据关联层级选择不同的标题和说明。",
)
add_table(
    doc,
    ["验证项目", "结果"],
    [
        ["后端自动测试", "52项全部通过"],
        ["前端类型检查", "通过"],
        ["前端生产构建", "通过"],
        ["非候选歌曲同类参考", "已增加专项测试"],
        ["受众反馈和接受机制", "已增加接口测试"],
        ["机制匹配案例", "已增加匹配结果和原因测试"],
    ],
    widths=[7.0, 9.2],
)

doc.add_heading("十二 当前完成程度和后续工作", level=1)
add_para(
    doc,
    "当前已经完成案例准入、首批严格案例、受众反馈结构、接受机制编码、首批20首候选音乐、六国区域矩阵和用户端结果展示。系统能够把案例证据、接受原因、候选音乐和国别方案串联起来。",
)
add_para(
    doc,
    "尚未完成的部分是真实六国受众实验。正式实验完成前，8项音乐潜力评分和国家偏好不能被视为实测结果。下一阶段应按照已经冻结的实验口径采集六国数据，完成原版与适配版比较，再将正式评分写入当前结果页面。",
)
add_para(
    doc,
    "因此，当前系统已经具备完整的研究成果展示框架和证据追溯能力，但正式跨国效果结论仍需六国实测数据支持。页面已经对候选结论、机制参考和实测结果作出明确区分。",
)

# Keep headings and tables stable across renderers.
for p in doc.paragraphs:
    if p.style and p.style.name.startswith("Heading"):
        p.paragraph_format.keep_with_next = True
    p.paragraph_format.widow_control = True

doc.core_properties.title = "智解国音国际传播功能建设汇报"
doc.core_properties.subject = "教师修改意见落实情况与系统实现说明"
doc.core_properties.author = "智解国音项目组"
doc.save(OUT)
print(OUT)
