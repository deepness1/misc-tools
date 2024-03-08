from bs4 import BeautifulSoup

import fetch


class Work:
    categories = {
        "RJ": "maniax",
        "BJ": "books",
        "VJ": "pro",
    }

    def convert_date(src):
        y_pos = src.find("年")
        m_pos = src.find("月")
        d_pos = src.find("日")
        if -1 in [y_pos, m_pos, d_pos]:
            raise Exception("invalid date")
        return "{}-{}-{}".format(
            src[:y_pos], src[y_pos + 1 : m_pos], src[m_pos + 1 : d_pos]
        )

    def __init__(self, pid):
        work = "work"
        category = Work.categories[pid[:2]]

        while work in ["work", "announce"]:
            url = f"https://www.dlsite.com/{category}/{work}/=/product_id/{pid}.html"
            res = fetch.request(url)
            if res != None:
                break
        if res == None:
            raise Exception("missing work")

        bs = BeautifulSoup(res.text, "html.parser")
        self.title = bs.body.find("h1").string
        self.date = Work.convert_date(
            bs.body.find("table", id="work_outline").tr.td.a.string
        )

        self.samples = []
        for s in bs.body.find("div", ref="product_slider_data").find_all(
            "div", recursive=False
        ):
            self.samples.append("https:" + s["data-src"])

        self.desc = ""
        for p in bs.body.find("div", itemprop="description").find_all(
            "div", recursive=False
        ):
            head = p.find("h3", class_="work_parts_heading")
            self.desc += "# {}\n".format(head.string if head != None else "")
            part = p.find("div", class_="work_parts_area")
            part_type = p["class"][1]
            if part_type == "type_text":
                self.desc += part.p.text + "\n"
            elif part_type == "type_image":
                for p in part.find_all("p"):
                    self.desc += p.text + "\n"
                for r in part.find_all("a"):
                    self.desc += "https:" + r["href"] + "\n"
            elif part_type == "type_multiimages":
                for i in part.ul.find_all(
                    "li", class_="work_parts_multiimage_item", recursive=False
                ):
                    text = i.find("div", class_="text")
                    if text != None:
                        self.desc += i.find("div", class_="text").p.text + "\n"
                    link = i.find("div", class_="image")
                    if link.a != None:
                        self.desc += "https:" + link.a["href"] + "\n"

            self.desc += "\n\n"

        self.desc = self.desc.strip()
