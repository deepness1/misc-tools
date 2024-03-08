import os


def truncate_by_concating(s, max_bytes):
    """
    Ensure that the UTF-8 encoding of a string has not more than
    max_bytes bytes
    :param s: The string
    :param max_bytes: Maximal number of bytes
    :return: The cut string
    """

    def len_as_bytes(s):
        return len(s.encode(errors="replace"))

    if len_as_bytes(s) <= max_bytes:
        return s

    res = ""
    for c in s:
        old = res
        res += c
        if len_as_bytes(res) > max_bytes:
            res = old
            break
    return res


def canonicalize_filename(s):
    return s.replace("/", "／")


def list_downloaded_works(recorddir):
    downloaded_path = os.path.join(recorddir, "downloaded")
    if not os.path.isfile(downloaded_path):
        return []

    result = []
    for l in open(downloaded_path, encoding="utf-8").readlines():
        l = l.strip()
        if len(l) == 0:
            continue
        result.append(l)

    return result


def append_downloaded_works(recorddir, work_id):
    current = list_downloaded_works(recorddir)
    if work_id in current:
        print("bug: attempt to append duplicated work")
        return
    current.append(work_id)
    downloaded_path = os.path.join(recorddir, "downloaded")
    file = open(downloaded_path, "w")
    for w in current:
        file.write(f"{w}\n")


def append_downloaded_works_fast(recorddir, work_id):
    os.makedirs(recorddir, exist_ok=True)
    downloaded_path = os.path.join(recorddir, "downloaded")
    open(downloaded_path, "a").write(f"{work_id}\n")
