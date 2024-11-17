import ell
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict
import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class MarkdownDocument(BaseModel):
    content: str = Field(description="The complete markdown content.")

    def update(self, additional_content: str) -> None:
        """Appends new content to the markdown document."""
        self.content += additional_content


# Define the ell function to convert wikitext to markdown
@ell.simple(model="gpt-4o", client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
def convert_wikitext_to_markdown(wikitext: str) -> str:
    """Convert wikitext to markdown without images."""
    prompt = f"""
Your task is to **convert the provided Wikitext chunk into perfectly formatted Markdown**, excluding any images. The output must **strictly adhere** to the rules outlined below to maintain the original content's structure and formatting as closely as possible.

### Conversion Instructions:

1. **Document Structure**:
   - **Title**: The first line must be the article's short name (e.g., "GRIA2" instead of "Glutamate Ionotropic Receptor AMPA Type Subunit 2") with a single `#`.
   - **Lead Section**: The first content section must use the heading `## Lead`.
   - **Other Sections**: All subsequent sections should use appropriate heading levels starting with `##`.
   - **Important**: Ensure each Markdown heading is on its own separate line, with the `#` symbols **not** attached to other text.

2. **Bold and Italic Text**:
   - **Bold**:
     - **Wikitext**: `'''bold text'''`
     - **Markdown**: `**bold text**`
   - **Italic**:
     - **Wikitext**: `''italic text''`
     - **Markdown**: `*italic text*`

3. **Links**:
   - **Internal Links**:
     - **Wikitext**: `[[Page|Display Text]]` or `[[Page]]`
     - **Markdown**: `[Display Text](https://en.wikipedia.org/wiki/Page)` or `[Page](https://en.wikipedia.org/wiki/Page)`
   - **External Links**:
     - Convert to Markdown link format if not already (e.g., `<http://example.com>` to `[http://example.com](http://example.com)`).

4. **Lists**:
   - **Bulleted Lists**:
     - **Wikitext**: Lines starting with `*`
     - **Markdown**: Lines starting with `-` or `*`
   - **Numbered Lists**:
     - **Wikitext**: Lines starting with `#`
     - **Markdown**: Lines starting with `1.`, `2.`, etc.
   - **Nested Lists**:
     - Maintain proper indentation for nested lists as per Markdown standards (using two spaces or a tab).

5. **References**:
   - **Remove** all reference numbers, footnotes, and `<sup>` tags from the content.

6. **Tables**:
   - **Markdown Format**:
     | Header 1 | Header 2 |
     |----------|----------|
     | Row1Cell1 | Row1Cell2 |
   - **Note**: Convert simple tables only. If a table is too complex, retain the plain text without table formatting.

7. **Exclude Images**:
   - **Remove** any image syntax such as `[[File:...]]`, `[[Image:...]]`, or similar entirely from the output.

8. **Templates**:
   - **Remove or Ignore** any templates (e.g., `{{Infobox...}}`, `{{Citation...}}`) present in the Wikitext.

9. **Code and Preformatted Text**:
   - **Wikitext Format**:
     - `<code>...code...</code>`
     - `<pre>...preformatted text...</pre>`
   - **Markdown Format**:
     ```
     ```language
     ...code...
     ```
     ```
     - Use appropriate language identifiers if available; otherwise, use plain code fences.
   - **Ensure** that code blocks are properly enclosed with triple backticks and maintain the original indentation and formatting.

10. **Other Formatting**:
    - **Horizontal Lines**: Convert `----` or `----` in Wikitext to `---` in Markdown.
    - **Blockquotes**: Convert `> ` in Wikitext to `> ` in Markdown.
    - **Em Dash and En Dash**: Replace Wikitext representations with proper Markdown characters if necessary.
    - **Special Characters**: Escape any Markdown-sensitive characters that are not intended to be formatted.

### Output Requirements:

- **No Explanations**: Do not include any explanations, comments, or additional text. **Provide only the converted Markdown content**.
- **Formatting Precision**: 
  - Ensure all Markdown headings are on separate lines, with `#` symbols **solely** used for headings.
  - Maintain proper spacing, indentation, and line breaks as per Markdown syntax.
- **File Saving**:
  - After conversion, **verify** that **every instruction** above has been meticulously followed.
  - **Save the output exclusively as a Markdown (`.md`) file** without any additional content.

### Verification Step:

Before saving, perform a thorough check to ensure that:

- **All headings**, bold, italic, links, lists, tables, and other formatting have been correctly converted.
- **No images or templates** are present in the Markdown output.
- **All reference numbers and `<sup>` tags** have been removed.
- **Code blocks** are properly formatted with code fences.
- **Overall structure and formatting** closely match the original Wikitext content.

### Input Data:

{wikitext}

"""

    return prompt


# Main function to process the text and convert to markdown
def convert_wikitext(wikitext: str) -> str:
    ell.init(store="./logdir", autocommit=True, verbose=False)
    current_state = MarkdownDocument(content="")

    raw_output = convert_wikitext_to_markdown(wikitext)

    markdown_output = raw_output.strip()
    new_markdown = markdown_output.replace("```markdown", "").replace("```", "").strip()

    try:
        current_state.update(new_markdown)
    except ValidationError as e:
        print(f"Validation error occurred: {e}")

    final_markdown = current_state.content.strip()
    print("MARKDOWN: ", final_markdown)

    return final_markdown


def parse_markdown_to_sections(markdown_content: str) -> List[Dict]:
    """
    Parse markdown content into sections.
    Returns a list of dictionaries containing section title, content, level (depth of the section), and index.
    """
    # Split the content into sections based on headers
    sections = []
    current_section = {"title": "", "content": [], "level": 0}
    current_index = 1

    # Split content into lines
    lines = markdown_content.split("\n")

    for line in lines:
        # Check if line is a header (starts with #)
        if line.strip().startswith("#"):
            # If we have a previous section, save it
            if current_section["title"]:
                sections.append(
                    {
                        "title": current_section["title"],
                        "content": "\n".join(current_section["content"]).strip(),
                        "level": current_section["level"],
                        "index": current_index,
                    }
                )
                current_index += 1
            # Start new section
            # Count #s to determine level
            level = len(re.match(r"^#+", line.strip()).group())
            # Remove #s and whitespace from title
            current_section = {
                "title": line.strip("#").strip(),
                "content": [],
                "level": level,
            }
        else:
            # Add content line to current section
            current_section["content"].append(line)

    # Add the last section if it exists
    if current_section["title"]:
        sections.append(
            {
                "title": current_section["title"],
                "content": "\n".join(current_section["content"]).strip(),
                "level": current_section["level"],
                "index": current_index,
            }
        )

    return sections


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using basic rules.
    """
    # Simple sentence splitting - can be enhanced based on needs
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


if __name__ == "__main__":
    # Example wikitext content
    wikitext_content = """ 
{{Short description|Mammalian protein found in Homo sapiens}}
{{Infobox_gene}}
'''Adenine phosphoribosyltransferase''' ('''APRTase''') is an [[enzyme]] encoded by the ''APRT'' [[gene]], found in [[humans]] on [[chromosome 16]].<ref name = "Valaperta_2014">{{cite journal | vauthors = Valaperta R, Rizzo V, Lombardi F, Verdelli C, Piccoli M, Ghiroldi A, Creo P, Colombo A, Valisi M, Margiotta E, Panella R, Costa E | title = Adenine phosphoribosyltransferase (APRT) deficiency: identification of a novel nonsense mutation | journal = BMC Nephrology | volume = 15 | pages = 102 | date = 1 July 2014 | pmid = 24986359 | doi = 10.1186/1471-2369-15-102 | pmc=4094445 | doi-access = free }}</ref> It is part of the Type I PRTase family and is involved in the [[nucleotide salvage]] pathway, which provides an alternative to [[nucleotide]] biosynthesis de novo in humans and most other animals.<ref name = "Silva_2008"/> In parasitic [[protozoa]] such as [[giardia]], APRTase provides the sole mechanism by which AMP can be produced.<ref>{{cite journal | vauthors = Sarver AE, Wang CC | title = The adenine phosphoribosyltransferase from Giardia lamblia has a unique reaction mechanism and unusual substrate binding properties | journal = The Journal of Biological Chemistry | volume = 277 | issue = 42 | pages = 39973–80 | date = Oct 2002 | pmid = 12171924 | doi = 10.1074/jbc.M205595200 | doi-access = free }}</ref> APRTase deficiency contributes to the formation of kidney stones ([[urolithiasis]]) and to potential [[renal failure|kidney failure]].<ref name ="Shi_2001">{{cite journal | vauthors = Shi W, Tanaka KS, Crother TR, Taylor MW, Almo SC, Schramm VL | title = Structural analysis of adenine phosphoribosyltransferase from Saccharomyces cerevisiae | journal = Biochemistry | volume = 40 | issue = 36 | pages = 10800–9 | date = Sep 2001 | pmid = 11535055 | doi=10.1021/bi010465h}}</ref>

[[File:APRT-CpG.svg|thumb|The APRT gene is constituted by 5 exons (in blue). The start (ATG) and stop (TGA) codons are indicated (bold blue). CpG dinucleotides are emphasized in red. They are more abundant in the upstream region of the gene where they form a [[CpG island]].]]

== Function ==

APRTase catalyzes the following reaction in the purine [[nucleotide salvage]] pathway:

[[Adenine]] + Phosphoribosyl Pyrophosphate ([[Phosphoribosyl pyrophosphate|PRPP]]) → Adenylate ([[Adenosine monophosphate|AMP]]) + Pyrophosphate ([[pyrophosphate|PPi]])

[[File:ARPTase Reaction Scheme.png|frame|center|ARPTase catalyzes a phosphoribosyl transfer from PRPP to adenine, forming AMP and releasing pyrophosphate (PPi).]]

In organisms that can synthesize [[purines]] de novo, the nucleotide salvage pathway provides an alternative that is  energetically more efficient. It can salvage adenine from the [[polyamine]] biosynthetic pathway or from dietary sources of purines.<ref name="Silva_2008">{{cite journal | vauthors = Silva CH, Silva M, Iulek J, Thiemann OH | title = Structural complexes of human adenine phosphoribosyltransferase reveal novel features of the APRT catalytic mechanism | journal = Journal of Biomolecular Structure & Dynamics | volume = 25 | issue = 6 | pages = 589–97 | date = Jun 2008 | pmid = 18399692 | doi = 10.1080/07391102.2008.10507205 | s2cid = 40788077 }}</ref> Although APRTase is functionally redundant in these organisms, it becomes more important during periods of rapid growth, such as embryogenesis and tumor growth.<ref name="Bashor_2002"/> It is constitutively expressed in all mammalian tissue.<ref name = "Silva_2004"/>

In [[protozoan]] parasites, the nucleotide salvage pathway provides the sole means for nucleotide synthesis. Since the consequences of APRTase deficiency in humans is comparatively mild and treatable, it may be possible to treat certain [[parasitic infections]] by targeting APRTase function.<ref>{{cite journal | vauthors = Shi W, Sarver AE, Wang CC, Tanaka KS, Almo SC, Schramm VL | title = Closed site complexes of adenine phosphoribosyltransferase from Giardia lamblia reveal a mechanism of ribosyl migration | journal = The Journal of Biological Chemistry | volume = 277 | issue = 42 | pages = 39981–8 | date = Oct 2002 | pmid = 12171925 | doi = 10.1074/jbc.M205596200 | doi-access = free }}</ref>

In [[plants]], as in other organisms, ARPTase functions primarily for the synthesis of [[adenylate]]. It has the unique ability to metabolize [[cytokinins]]—a [[plant hormone]] that can exist as a [[base (chemistry)|base]], [[nucleotide]], or [[nucleoside]]—into adenylate nucleotides.<ref name = "Allen_2002">{{cite journal | vauthors = Allen M, Qin W, Moreau F, Moffatt B | title = Adenine phosphoribosyltransferase isoforms of Arabidopsis and their potential contributions to adenine and cytokinin metabolism | journal = Physiologia Plantarum | volume = 115 | issue = 1 | pages = 56–68 | date = May 2002 | pmid = 12010467 | doi=10.1034/j.1399-3054.2002.1150106.x}}</ref>

APRT is functionally related to [[hypoxanthine-guanine phosphoribosyltransferase]] (HPRT).

==Structure==

APRTase is a [[homodimer]], with 179 [[amino acid]] residues per [[monomer]]. Each monomer contains the following regions:
[[File:Flexible loop and Hood domains of human APRTase.png|thumb|left|Catalytic site of APRTase with reactants adenine and PRPP resolved. The Hood is believed to be important for purine specificity, while the flexible loop is thought to contain the molecules within the active site.]]
* "Core" domain (residues 33-169) with five parallel [[Beta sheet|β-sheets]]
* "Hood" domain (residues 5-34) with 2 [[Alpha helix|α-helices]] and 2 β-sheets
* "Flexible loop" domain (residues 95-113) with 2 antiparallel β-sheets<ref name = "Silva_2004"/>

[[File:Human APRTase, adenine binding site.png|thumb|right|Residues A131, L159, V25, and R27 are important for purine specificity in human APRTase.]]

The core is highly conserved across many PRTases. The hood, which contains the [[adenine]] [[binding site]], has more variability within the family of enzymes. A 13-residue motif comprises the [[Phosphoribosyl pyrophosphate|PRPP]] binding region and involves two adjacent [[acidic]] residues and at least one surrounding [[hydrophobic]] residue.<ref name = "Liu_1990">{{cite journal | vauthors = Liu Q, Hirono S, Moriguchi I | title = Quantitative structure-activity relationships for calmodulin inhibitors | journal = Chemical & Pharmaceutical Bulletin | volume = 38 | issue = 8 | pages = 2184–9 | date = Aug 1990 | pmid = 2279281 | doi=10.1248/cpb.38.2184| doi-access = free }}</ref>

The enzyme's specificity for adenine involves hydrophobic residues [[Alanine|Ala131]] and [[Leucine|Leu159]] in the core domain. In humans, two residues in the hood domain [[hydrogen bond]] with the purine for further specificity: [[Valine|Val25]] with the [[hydrogen]]s on N6, and [[Arginine|Arg27]] with N1. Although the flexible loop does not interact with the hood during purine recognition, it is thought to close over the [[active site]] and sequester the reaction from [[solvents]].<ref name = "Silva_2004">{{cite journal | vauthors = Silva M, Silva CH, Iulek J, Thiemann OH | title = Three-dimensional structure of human adenine phosphoribosyltransferase and its relation to DHA-urolithiasis | journal = Biochemistry | volume = 43 | issue = 24 | pages = 7663–71 | date = Jun 2004 | pmid = 15196008 | doi = 10.1021/bi0360758 }}</ref>

Most research on APRTase reports that Mg<sup>2+</sup> is essential for phosphoribosyl transfer, and this is conserved across Type I PRTases.<ref name = "Allen_2002"/> However, a recent effort to resolve the structure of human APRTase was unable to locate a single site for Mg<sup>2+</sup>, but did find evidence to suggest a Cl<sup>−</sup> atom near Trp98. Despite the difficulty of placing Mg<sup>2+</sup>, it is generally accepted that the [[catalytic mechanism]] is dependent on this ion.<ref name="Silva_2008"/>

==Mechanism==

APRTase proceeds via a bi bi ordered sequential mechanism, involving the formation of a ternary complex. The enzyme first binds [[phosphoribosyl pyrophosphate|PRPP]], followed by [[adenine]]. After the phosphoribosyl transfer occurs, [[pyrophosphate]] leaves first, followed by [[Adenosine monophosphate|AMP]]. Kinetic studies indicate that the phosphoribosyl transfer is relatively fast, while the product release (particularly the release of AMP) is [[rate-determining step|rate-limiting]].<ref name = "Bashor_2002">{{cite journal | vauthors = Bashor C, Denu JM, Brennan RG, Ullman B | title = Kinetic mechanism of adenine phosphoribosyltransferase from Leishmania donovani | journal = Biochemistry | volume = 41 | issue = 12 | pages = 4020–31 | date = Mar 2002 | pmid = 11900545 | doi=10.1021/bi0158730}}</ref>

In human APRTase, it is thought that adenine's N9 proton is abstracted by [[Glutamic acid|Glu104]] to form an oxacarbenium [[transition state]]. This functions as the [[nucleophile]] to attack the [[anomeric]] carbon of PRPP, forming AMP and displacing pyrophosphate from PRPP. The mechanism of APRTase is generally consistent with that of other PRTases, which conserve the function of displacing PRPP's α-1-pyrophosphate using a [[nitrogen]] nucleophile, in either an S<sub>N</sub>1 or S<sub>N</sub>2 attack.<ref name="Silva_2008"/>

==Deficiency==

When APRTase has reduced or nonexistent activity, [[adenine]] accumulates from other pathways. It is degraded by [[xanthine dehydrogenase]] to [[2,8-dihydroxyadenine]] (DHA). Although DHA is protein-bound in [[blood plasma|plasma]], it has poor [[solubility]] in [[urine]] and gradually precipitates in [[nephrons|kidney tubules]], leading to the formation of kidney stones ([[urolithiasis]]). If left untreated, the condition can eventually produce [[renal failure|kidney failure]].<ref name ="Shi_2001"/>

ARPTase deficiency was first diagnosed in the [[UK]] in 1976. Since then, two categories of APRTase deficiency have been defined in humans.<ref name = "Cassidy_2004">{{cite journal | vauthors = Cassidy MJ, McCulloch T, Fairbanks LD, Simmonds HA | title = Diagnosis of adenine phosphoribosyltransferase deficiency as the underlying cause of renal failure in a renal transplant recipient | journal = Nephrology, Dialysis, Transplantation | volume = 19 | issue = 3 | pages = 736–8 | date = Mar 2004 | pmid = 14767036 | doi=10.1093/ndt/gfg562| doi-access = free }}</ref>

Type I deficiency results in a complete loss of APRTase activity and can occur in patients that are [[homozygous]] or [[compound heterozygous]] for various [[mutations]].<ref name = "Bollée_2012">{{cite journal | vauthors = Bollée G, Harambat J, Bensman A, Knebelmann B, Daudon M, Ceballos-Picot I | title = Adenine phosphoribosyltransferase deficiency | journal = Clinical Journal of the American Society of Nephrology | volume = 7 | issue = 9 | pages = 1521–7 | date = Sep 2012 | pmid = 22700886 | doi = 10.2215/CJN.02320312 | doi-access = free }}</ref> [[Sequencing]] has revealed many different mutations that can account for Type 1, including [[missense mutations]], [[nonsense mutations]], a duplicated set of 4 [[base pairs]] in [[exon]] 3,<ref>{{cite journal | vauthors = Kamatani N, Hakoda M, Otsuka S, Yoshikawa H, Kashiwazaki S | title = Only three mutations account for almost all defective alleles causing adenine phosphoribosyltransferase deficiency in Japanese patients | journal = The Journal of Clinical Investigation | volume = 90 | issue = 1 | pages = 130–5 | date = Jul 1992 | pmid = 1353080 | doi = 10.1172/JCI115825 | pmc=443071}}</ref> and a single [[thymine]] [[Insertion (genetics)|insertion]] in [[intron]] 4.<ref name = "Bollée_2010">{{cite journal | vauthors = Bollée G, Dollinger C, Boutaud L, Guillemot D, Bensman A, Harambat J, Deteix P, Daudon M, Knebelmann B, Ceballos-Picot I | title = Phenotype and genotype characterization of adenine phosphoribosyltransferase deficiency | journal = Journal of the American Society of Nephrology | volume = 21 | issue = 4 | pages = 679–88 | date = Apr 2010 | pmid = 20150536 | doi = 10.1681/ASN.2009080808 | pmc=2844298}}</ref> These mutations cause effects that are clustered into three main areas: in the binding of PRPP's β-phosphate, in the binding of PRPP's 5'-phosphate, and in the segment of the flexible loop that closes over the active site during catalysis <ref name = "Silva_2004"/> 
Type I deficiency has been observed in various ethnic groups but studied predominately among [[White people|White]] populations.<ref name = "Bollée_2010"/>

Type II deficiency causes APRTase to have a reduced affinity for PRPP, resulting in a tenfold increase in the K<sub>M</sub> value.<ref name = "Silva_2008"/> It has been observed and studied primarily in [[Japan]].<ref name = "Bollée_2010"/>

A diagnosis of APRTase deficiency can be made by analyzing [[kidney stones]], measuring DHA concentrations in urine, or analyzing APRTase activity in [[erythrocytes]]. It is treatable with regular doses of [[allopurinol]] or [[febuxostat]], which inhibit xanthine dehydrogenase activity to prevent the accumulation and precipitation of DHA.<ref name = "Edvardsson_1993">{{cite journal | vauthors =  Edvardsson VO, Palsson R, Sahota A | veditors = Pagon RA, Adam MP, Ardinger HH, Wallace SE, Amemiya A, Bean LJ, Bird TD, Fong CT, Mefford HC, Smith RJ, Stephens K | journal =  SourceGeneReviews | title = Adenine Phosphoribosyltransferase Deficiency | date = 1993 | pmid = 22934314 }}</ref> The condition can also be attenuated with a low-purine diet and high fluid intake.<ref name = "Cassidy_2004"/>


    """

    # Convert wikitext to markdown
    markdown_content = convert_wikitext(wikitext_content)
    sections = parse_markdown_to_sections(markdown_content)

    for section in sections:
        if section["content"]:
            section["sentences"] = split_into_sentences(section["content"])
        else:
            section["sentences"] = []

    with open("APRT-wikipedia.json", "w") as a:
        json.dump(sections, a, indent=4)
