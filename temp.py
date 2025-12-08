import json
import re

def generate_synthetic_output(text: str):
    out = []
    text_norm = text.replace("°", " độ").replace("Δ", "tam giác ").strip()
    text_lower = text_norm.lower()

    # ============================================================
    # 1. GOAL (Mục tiêu)
    # ============================================================
    goal_text = text_norm
    for kw in ["Chứng minh rằng", "Chứng minh", "CMR", "CM", "Tìm", "Xác định"]:
        if kw in text_norm:
            goal_text = text_norm.split(kw, 1)[-1]
            break

    for m in re.finditer(r'tứ giác\s+([A-Z]{4})', goal_text, re.IGNORECASE):
        pts = list(m.group(1).upper())
        out.append({"type": "RENDER_ORDER", "subtype": "CYCLIC_QUAD", "points": pts})

    multi = re.search(r'(\d+)\s+điểm\s+([^\.]+?)\s+cùng thuộc', goal_text, re.IGNORECASE)
    if multi:
        pts_str = multi.group(2).upper()
        pts = re.findall(r'\b[A-Z]\b', pts_str)
        if len(pts) >= 4:
            out.append({"type": "RENDER_ORDER", "subtype": "CONCYCLIC_POINTS", "points": pts})

    # ============================================================
    # 2. TAM GIÁC
    # ============================================================
    triangles_found = []
    for m in re.finditer(r'tam giác\s+([A-Z]{3})', text_norm, re.IGNORECASE):
        pts_str = m.group(1).upper()
        points = list(pts_str)
        t_type = "ACUTE"
        context = text_norm[max(0, m.start()-30):min(len(text_norm), m.end()+30)].lower()
        if "vuông" in context: t_type = "RIGHT"
        elif "đều" in context: t_type = "EQUILATERAL"
        elif "cân" in context: t_type = "ISOSCELES"
        elif "tù" in context or "> 90" in context: t_type = "OBTUSE"
        
        out.append({"type": "TRIANGLE", "points": points, "property": t_type})
        triangles_found.append(points)

    # ============================================================
    # 3. ĐƯỜNG CAO
    # ============================================================
    def find_base_line(vertex_h, triangles):
        for tri_pts in triangles:
            if vertex_h in tri_pts:
                base = [p for p in tri_pts if p != vertex_h]
                if len(base) == 2: return "".join(sorted(base))
        return "UNKNOWN"

    for m in re.finditer(r'đường cao\s+([A-Z]{2})', text_norm, re.IGNORECASE):
        seg = m.group(1).upper()
        vertex = seg[0]
        foot = seg[1]
        base = find_base_line(vertex, triangles_found)
        out.append({"type": "ALTITUDE", "segment": seg, "vertex": vertex, "foot": foot, "base_line": base}) 

    # ============================================================
    # 4. GIAO ĐIỂM & CẮT NHAU
    # ============================================================
    seg_pattern = r'(?:[A-Z]{2}|[A-Z]x|[A-Z]y|d)'
    
    cut_matches = re.finditer(rf'({seg_pattern})\s+cắt\s+({seg_pattern})\s+tại\s+([A-Z])\b', text_norm, re.IGNORECASE)
    for m in cut_matches:
        out.append({"type": "INTERSECTION", "point": m.group(3).upper(), "lines": [m.group(1), m.group(2)]})

    cut_mutual = re.finditer(rf'({seg_pattern})(?:\s+và\s+|,\s*)({seg_pattern})\s+cắt\s+(?:nhau\s+)?tại\s+([A-Z])\b', text_norm, re.IGNORECASE)
    for m in cut_mutual:
        out.append({"type": "INTERSECTION", "point": m.group(3).upper(), "lines": [m.group(1), m.group(2)]})

    def_inter = re.finditer(rf'([A-Z])\b\s+là\s+giao điểm\s+(?:của\s+)?({seg_pattern})\s+(?:và|với)\s+({seg_pattern})', text_norm, re.IGNORECASE)
    for m in def_inter:
        out.append({"type": "INTERSECTION", "point": m.group(1).upper(), "lines": [m.group(2), m.group(3)]})
    
    circle_cut = re.finditer(rf'({seg_pattern})\s+cắt\s+(?:đường tròn|nửa đường tròn|\(O\))\s+tại\s+([A-Z])\b', text_norm, re.IGNORECASE)
    for m in circle_cut:
        out.append({"type": "INTERSECTION_CIRCLE", "point": m.group(2).upper(), "line": m.group(1), "circle": "O"})

    # ============================================================
    # 5. VUÔNG GÓC
    # ============================================================
    perp_matches = re.finditer(r'([A-Z]{2})\s*(?:vuông góc|⊥)\s*(?:với|tại|lên)?\s*([A-Z]{2})', text_norm, re.IGNORECASE)
    for m in perp_matches:
        out.append({"type": "PERPENDICULAR", "lines": [m.group(1).upper(), m.group(2).upper()]})

    construct_perp = re.finditer(r'[Kk]ẻ\s+([A-Z]{2})\s+vuông góc.*?\s+([A-Z]{2})', text_norm)
    for m in construct_perp:
        out.append({"type": "PERPENDICULAR", "lines": [m.group(1).upper(), m.group(2).upper()]})

    # ============================================================
    # 6. HÌNH CHIẾU
    # ============================================================
    proj_matches = re.finditer(r'([A-Z])\s+là\s+hình chiếu.*?([A-Z])\s+lên\s+([A-Z]{2})', text_norm, re.IGNORECASE)
    for m in proj_matches:
        point_proj = m.group(1).upper()
        point_source = m.group(2).upper()
        base_line = m.group(3).upper()
        segment = point_source + point_proj
        out.append({"type": "PERPENDICULAR", "lines": [segment, base_line], "origin_text": "projection"})

    # ============================================================
    # 7. SONG SONG
    # ============================================================
    para_matches = re.finditer(r'([A-Z]{2})\s*(?:song song|//)\s*(?:với)?\s*([A-Z]{2})', text_norm, re.IGNORECASE)
    for m in para_matches:
        out.append({"type": "PARALLEL", "lines": [m.group(1).upper(), m.group(2).upper()]})

    # ============================================================
    # 8. TRUNG ĐIỂM
    # ============================================================
    m_mid_1 = re.finditer(r'\b([A-Z])\b\s+là\s+trung điểm\s+(?:của\s+)?([A-Z]{2})', text_norm, re.IGNORECASE)
    for m in m_mid_1:
        out.append({"type": "MIDPOINT", "point": m.group(1).upper(), "segment": m.group(2).upper()})

    m_mid_2 = re.finditer(r'trung điểm\s+([A-Z])\b\s+(?:của\s+)?(?:dây|cạnh|đoạn)?\s*([A-Z]{2})', text_norm, re.IGNORECASE)
    for m in m_mid_2:
        out.append({"type": "MIDPOINT", "point": m.group(1).upper(), "segment": m.group(2).upper()})

    # ============================================================
    # 9. ĐIỂM ĐẶC BIỆT & ĐƯỜNG TRÒN
    # ============================================================
    if "trực tâm" in text_lower:
        h_match = re.search(r'trực tâm\s+([A-Z])', text_norm, re.IGNORECASE)
        h_point = h_match.group(1).upper() if h_match else "H"
        out.append({"type": "ORTHOCENTER", "point": h_point})

    if "tâm đường tròn" in text_lower:
        center_m = re.search(r'tâm\s+(?:đường tròn\s+)?([A-Z])', text_norm, re.IGNORECASE)
        if center_m:
            out.append({"type": "CENTER", "point": center_m.group(1).upper()})

    if "đường tròn (O)" in text_norm or "tâm O" in text_norm:
        out.append({"type": "CIRCLE", "center": "O"})
    
    if "nửa đường tròn" in text_lower:
        out.append({"type": "SEMICIRCLE", "center": "O"})

    tangent_raw = re.finditer(r'tiếp tuyến\s+([A-Z]{2}(?:,\s*[A-Z]{2})*)', text_norm, re.IGNORECASE)
    for m in tangent_raw:
        lines = m.group(1).replace(" ", "").split(",")
        for line in lines:
            out.append({"type": "TANGENT", "line": line})
    
    tangent_ray = re.finditer(r'tiếp tuyến\s+([A-Z]x|[A-Z]y)', text_norm, re.IGNORECASE)
    for m in tangent_ray:
        out.append({"type": "TANGENT", "line": m.group(1)})

    tangent_at = re.finditer(r'tiếp tuyến\s+(?:tại|của)\s+([A-Z])', text_norm, re.IGNORECASE)
    for m in tangent_at:
        out.append({"type": "TANGENT_POINT", "point": m.group(1).upper()})

    # ============================================================
    # 10. ĐỊNH NGHĨA ĐIỂM (CẬP NHẬT LOGIC NHẬN DIỆN TÊN ĐƯỜNG TRÒN)
    # ============================================================
    
    def get_circle_name(ctx):
        # ctx là đoạn văn bản sau chữ "đường tròn", ví dụ: "(O)", "ngoại tiếp tam giác ABC"
        ctx_clean = ctx.replace("\n", " ").strip()
        
        # 1. Ưu tiên: Tìm tâm cụ thể (O), (I), tâm K
        m_center = re.search(r'(?:\(|tâm\s+)([A-Z0-9\']+)', ctx_clean, re.IGNORECASE)
        if m_center:
            return m_center.group(1).upper()
            
        # 2. Tìm theo đa giác ngoại tiếp (ABCD, ABC...)
        # Bắt các từ khóa: ngoại tiếp, đi qua
        # Regex tìm chuỗi chữ cái in hoa liên tiếp độ dài >= 3 (ABC, ABCD, MNPQ...)
        m_poly = re.search(r'(?:ngoại tiếp|đi qua).*?([A-Z]{3,5})', ctx_clean, re.IGNORECASE)
        if m_poly:
            return m_poly.group(1).upper()
            
        # 3. Mặc định
        return "O"

    # Regex chung để bắt ngữ cảnh sau "đường tròn"
    # Nó sẽ cố gắng bắt một đoạn text đủ dài sau chữ "đường tròn" để function get_circle_name phân tích
    circle_context_pattern = r'((?:đường tròn|nửa đường tròn|đt|cung)\s*[^,\.;]*)'

    # Dạng 1: Nằm NGOÀI
    p_outside = re.finditer(rf'(?:điểm\s+)?([A-Z])\s+(?:nằm\s+)?(?:ở\s+)?(?:bên\s+)?ngoài\s+{circle_context_pattern}', text_norm, re.IGNORECASE)
    for m in p_outside:
        out.append({
            "type": "POINT", 
            "name": m.group(1).upper(), 
            "location": "OUTSIDE_CIRCLE", 
            "circle": get_circle_name(m.group(2))
        })

    # Dạng 2: Nằm TRÊN/THUỘC
    p_on_circle = re.finditer(rf'(?:điểm\s+)?([A-Z])\s+(?:nằm\s+)?(?:trên|thuộc)\s+{circle_context_pattern}', text_norm, re.IGNORECASE)
    for m in p_on_circle:
        out.append({
            "type": "POINT", 
            "name": m.group(1).upper(), 
            "location": "ON_CIRCLE", 
            "circle": get_circle_name(m.group(2))
        })

    # Dạng 3: Nằm trên CẠNH/ĐOẠN (Giữ nguyên)
    p_on_line = re.finditer(r'(?:điểm\s+)?([A-Z])\s+(?:nằm\s+)?(?:trên|thuộc)\s+(?:cạnh|đoạn|đường thẳng|tia)\s+([A-Z]{2}|[A-Z]x|[A-Z]y)', text_norm, re.IGNORECASE)
    for m in p_on_line:
        out.append({
            "type": "POINT", 
            "name": m.group(1).upper(), 
            "location": "ON_LINE", 
            "line": m.group(2)
        })

    # Dạng 4: Điểm bất kỳ (Giữ nguyên)
    p_generic = re.finditer(r'(?:Cho|Lấy)\s+(?:điểm\s+)?([A-Z])\b', text_norm, re.IGNORECASE)
    for m in p_generic:
        point = m.group(1).upper()
        is_defined = False
        for item in out:
            if item.get("type") == "POINT" and item.get("name") == point:
                is_defined = True
                break
        if not is_defined:
             out.append({"type": "POINT", "name": point, "location": "ARBITRARY"})

    # ============================================================
    # 11. CLEAN UP
    # ============================================================
    seen = set()
    final = []
    for item in out:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            final.append(item)
            
    return final

# ====================== DATASET ======================
all_problems = [
  "Cho tam giác ABC nhọn có các đường cao BD và CE cắt nhau tại H. Chứng minh rằng tứ giác BCDE và tứ giác ADHE là các tứ giác nội tiếp.",
  "Cho đường tròn (O) và điểm A nằm bên ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC với đường tròn (B, C là các tiếp điểm). Chứng minh tứ giác ABOC nội tiếp đường tròn.",
  "Cho tam giác ABC vuông tại A, đường cao AH. Kẻ HE vuông góc với AB tại E, HF vuông góc với AC tại F. Chứng minh tứ giác AEHF nội tiếp đường tròn.",
  "Cho nửa đường tròn (O) đường kính AB. Lấy điểm M trên nửa đường tròn. Kẻ tiếp tuyến Ax. Tia BM cắt Ax tại I. Tia phân giác của góc IAM cắt nửa đường tròn tại E, cắt tia BM tại F. Tia BE cắt Ax tại H, cắt AM tại K. Chứng minh tứ giác EFMK nội tiếp.",
  "Từ điểm M nằm ngoài đường tròn (O) kẻ hai tiếp tuyến MA, MB (A, B là tiếp điểm) và cát tuyến MCD không đi qua tâm O (C nằm giữa M và D). Gọi I là trung điểm của dây CD. Chứng minh 5 điểm M, A, I, O, B cùng thuộc một đường tròn.",
  "Cho tam giác ABC có ba góc nhọn nội tiếp đường tròn (O). Các đường cao AD, BE, CF cắt nhau tại H. Chứng minh tứ giác BFEC nội tiếp và H là tâm đường tròn nội tiếp tam giác DEF.",
  "Cho hình vuông ABCD. Trên cạnh BC lấy điểm E, trên cạnh CD lấy điểm F sao cho góc EAF = 45 độ. Hạ AH vuông góc với EF tại H. Chứng minh tứ giác ABHE và ADHF là các tứ giác nội tiếp.",
  "Cho tứ giác ABCD nội tiếp đường tròn (O). Gọi M là điểm chính giữa của cung AB. Dây CM và DM cắt dây AB lần lượt tại P và Q. Chứng minh tứ giác CDQP nội tiếp.",
  "Cho tam giác ABC vuông tại A. Trên cạnh AC lấy điểm M, dựng đường tròn tâm I đường kính MC. Đường tròn này cắt BC tại E. Đường thẳng BM cắt đường tròn (I) tại D. Chứng minh tứ giác ABCD nội tiếp.",
  "Cho đường tròn tâm O. Từ điểm A ở bên ngoài đường tròn vẽ hai tiếp tuyến AB và AC. Trên BC lấy điểm M. Vẽ đường thẳng vuông góc với OM tại M cắt AB và AC lần lượt tại E và D. Chứng minh các tứ giác EBOM và DCMO nội tiếp.",
  "Cho tam giác ABC cân tại A. Các trung tuyến AH, BE, CF cắt nhau tại G. Gọi M là trung điểm của BG, N là trung điểm của FG. Chứng minh rằng tứ giác CMNE nội tiếp.",
  "Cho hình bình hành ABCD (có góc A > 90 độ). Các đường cao kẻ từ A cắt BC tại K và cắt CD tại I. Chứng minh tứ giác AKCI nội tiếp đường tròn.",
  "Cho tam giác ABC vuông tại A. Kẻ đường cao AH. Vẽ đường tròn đường kính AH cắt AB tại E, cắt AC tại F. Chứng minh tứ giác BCFE nội tiếp.",
  "Cho đường tròn (O) đường kính AB. Lấy điểm C thuộc đường tròn. Tiếp tuyến tại A của (O) cắt đường thẳng BC tại D. Gọi H là trung điểm của AD. Chứng minh tứ giác AHCO nội tiếp.",
  "Cho hai đường tròn (O) và (O') cắt nhau tại A và B. Một cát tuyến qua A cắt (O) tại C và cắt (O') tại D. Tiếp tuyến tại C của (O) và tiếp tuyến tại D của (O') cắt nhau tại M. Chứng minh tứ giác MCBD nội tiếp.",
  "Cho tam giác ABC nhọn (AB < AC) nội tiếp đường tròn (O). Các đường cao AD, BE, CF cắt nhau tại H. Gọi K là giao điểm của EF và BC. Chứng minh tứ giác KFDO nội tiếp.",
  "Cho nửa đường tròn tâm O đường kính AB. C là một điểm nằm trên nửa đường tròn. H là hình chiếu của C trên AB. Qua trung điểm M của CH, kẻ đường thẳng vuông góc với OC, cắt nửa đường tròn tại D và E. Chứng minh tứ giác ABDE nội tiếp.",
  "Cho tam giác ABC nhọn nội tiếp đường tròn (O). Gọi H là trực tâm của tam giác. Kẻ đường kính AD của đường tròn. Gọi M là hình chiếu của B lên AD, N là hình chiếu của C lên AD. Chứng minh tứ giác BMNC nội tiếp.",
  "Cho hình chữ nhật ABCD. Gọi M, N, P lần lượt là hình chiếu vuông góc của C lên các đường thẳng BD, AD và AB. Chứng minh 4 điểm M, N, P và tâm O của hình chữ nhật cùng thuộc một đường tròn.",
  "Cho đường tròn (O) và dây cung BC cố định. Điểm A di động trên cung lớn BC. Các đường cao AD, BE, CF của tam giác ABC cắt nhau tại H. Chứng minh đường tròn ngoại tiếp tứ giác BFEC luôn đi qua hai điểm cố định.",
  "Cho đường tròn (O; R) có đường kính AB. Bán kính CO vuông góc với AB, M là một điểm bất kỳ trên cung nhỏ AC; BM cắt AC tại H. Gọi K là hình chiếu của H trên AB. Chứng minh tứ giác CBKH nội tiếp.",
  "Cho tam giác ABC nhọn nội tiếp đường tròn (O). Vẽ đường kính AD. Đường thẳng qua B vuông góc với AD tại E cắt AC tại F. Gọi H là hình chiếu vuông góc của B trên AC. Chứng minh tứ giác EFHC nội tiếp.",
  "Cho đường tròn (O) đường kính AB = 2R. Gọi d1 và d2 lần lượt là các tiếp tuyến tại A và B. Gọi I là trung điểm của OA, E là điểm thuộc đường tròn. Đường thẳng d đi qua E vuông góc với EI cắt d1, d2 lần lượt tại M, N. Chứng minh tứ giác AMEI nội tiếp.",
  "Cho tam giác ABC vuông tại A. Trên nửa mặt phẳng bờ BC chứa điểm A, vẽ nửa đường tròn đường kính BH cắt AB tại E, nửa đường tròn đường kính HC cắt AC tại F. Chứng minh tứ giác BEFC nội tiếp.",
  "Cho đường tròn (O) và dây BC cố định. Điểm A di chuyển trên cung lớn BC. Các đường cao BD và CE cắt nhau tại H. Gọi K là giao điểm của DE và BC. Chứng minh tứ giác ADHE nội tiếp.",
  "Cho đường tròn (O) và điểm M nằm ngoài đường tròn. Qua M kẻ các tiếp tuyến MA, MB. Gọi C là điểm bất kỳ trên cung nhỏ AB. Gọi D, E, F lần lượt là hình chiếu vuông góc của C trên AB, AM, BM. Chứng minh tứ giác AECD nội tiếp.",
  "Cho tam giác ABC nhọn. Các đường cao BD và CE cắt nhau tại H. Qua D kẻ đường thẳng song song với AC cắt AB tại I và cắt EB tại F. Chứng minh tứ giác BCDE nội tiếp.",
  "Cho nửa đường tròn (O) đường kính AB. Gọi C là điểm chính giữa của cung AB. M là điểm bất kỳ trên cung AC. Tiếp tuyến tại M cắt các tiếp tuyến tại A và B lần lượt ở D và E. Chứng minh tứ giác ADMO nội tiếp.",
  "Cho tam giác ABC cân tại A nội tiếp đường tròn (O). Điểm M thuộc cung nhỏ AC. Kẻ Mx vuông góc với AM cắt tia BC tại N. Chứng minh tứ giác AMNC nội tiếp.",
  "Cho tam giác ABC vuông ở A. Trên AC lấy điểm M và vẽ đường tròn đường kính MC. Kẻ BM cắt đường tròn tại D. Chứng minh tứ giác ABCD nội tiếp.",
  "Cho tứ giác ABCD nội tiếp đường tròn (O) đường kính AD. Kẻ EF vuông góc với AD tại F (E là giao điểm hai đường chéo). Chứng minh tứ giác ABEF nội tiếp.",
  "Cho hình vuông ABCD. Lấy điểm M trên cạnh BC. Đường thẳng qua A vuông góc với AM cắt đường thẳng CD tại N. Gọi I là trung điểm của MN. Kẻ đường cao AH của tam giác AMN. Chứng minh tứ giác AHCD nội tiếp.",
  "Cho đường tròn (O; R). Cát tuyến d cắt đường tròn tại A và B. Từ M trên d kẻ hai tiếp tuyến MC và MD. Gọi I là trung điểm của AB. Chứng minh tứ giác MCID nội tiếp.",
  "Cho tam giác ABC đều nội tiếp đường tròn (O). M là điểm di động trên cung nhỏ BC. Trên đoạn MA lấy điểm D sao cho MD = MB. Chứng minh tứ giác ADOC nội tiếp.",
  "Cho nửa đường tròn tâm O đường kính AB. Từ A và B vẽ các tiếp tuyến Ax và By. Đường thẳng qua N thuộc nửa đường tròn vuông góc với NM cắt Ax, By tại C và D. Chứng minh tứ giác ACMN nội tiếp.",
  "Cho tam giác ABC vuông tại A. Từ một điểm E trên cạnh AC kẻ đường thẳng vuông góc xuống BC tại M. Chứng minh tứ giác ABME nội tiếp.",
  "Cho đường tròn tâm O, đường kính AB. Kẻ tiếp tuyến d tại B. Gọi M là điểm chạy trên d. AM cắt (O) tại C. Gọi H là trung điểm của AC. Chứng minh tứ giác OBHM nội tiếp.",
  "Cho hình thang cân ABCD nội tiếp đường tròn (O). Kẻ các đường cao AH, BK. Chứng minh tứ giác ABKH nội tiếp.",
  "Cho tam giác ABC có 3 góc nhọn. Đường tròn tâm O đường kính BC cắt AB, AC tại F, E. BE cắt CF tại H. Gọi K là điểm đối xứng của H qua BC. Chứng minh tứ giác ACKB nội tiếp.",
  "Cho tam giác ABC vuông tại A. Kẻ đường cao AH. Gọi I, K lần lượt là tâm đường tròn nội tiếp các tam giác ABH và ACH. Đường thẳng IK cắt AB, AC tại M và N. Chứng minh tứ giác AMHN nội tiếp.",
  "Cho nửa đường tròn tâm O đường kính AB. Điểm C nằm trên nửa đường tròn. Gọi D là điểm chính giữa cung AC. Dây AC cắt BD tại H. Dây AD cắt BC tại K. Chứng minh tứ giác CDKH nội tiếp.",
  "Cho tam giác ABC nhọn nội tiếp đường tròn (O). Kẻ MH vuông góc với AB, MK vuông góc với AC (M thuộc cung nhỏ BC). Chứng minh tứ giác AHMK nội tiếp.",
  "Cho điểm M thuộc đường tròn (O), tiếp tuyến tại M cắt tiếp tuyến tại A và B của đường tròn lần lượt ở C và D (AB là đường kính). Chứng minh tứ giác CDMO nội tiếp.",
  "Cho tam giác ABC vuông cân tại A. M là trung điểm BC. Điểm E thuộc đoạn MC. Kẻ BH, CK vuông góc với AE. Chứng minh tứ giác ABHK nội tiếp.",
  "Cho tam giác ABC nhọn. Vẽ đường tròn tâm O đường kính BC cắt AB tại D và AC tại E. BE và CD cắt nhau tại H. Chứng minh tứ giác ADHE nội tiếp.",
  "Cho hình vuông ABCD. Gọi E là một điểm trên cạnh BC. Qua A kẻ đường thẳng vuông góc với AE cắt đường thẳng CD tại F. Chứng minh tứ giác AEFD có các điểm cùng thuộc một đường tròn (biến thể nội tiếp).",
  "Cho tam giác ABC vuông tại A. Kẻ đường cao AH. Gọi D và E lần lượt là hình chiếu của H trên AB và AC. Chứng minh tứ giác BDEC nội tiếp.",
  "Cho đường tròn (O) đường kính AB. M là một điểm trên đường tròn. Tiếp tuyến tại M cắt tiếp tuyến tại A ở C. Chứng minh tứ giác ACMO nội tiếp.",
  "Cho tam giác nhọn ABC. Gọi M là trung điểm của BC. Các đường trung trực của AB và AC cắt nhau tại O. Gọi H là trực tâm của tam giác ABC. Chứng minh tứ giác OBHC nội tiếp (trường hợp đặc biệt).",
  "Cho hai đường tròn (O) và (O') cắt nhau tại A và B. Gọi I là trung điểm của OO'. Đường thẳng qua A cắt các đường tròn tại C và D. Chứng minh tứ giác OO'DC có tính chất liên quan nội tiếp khi biến đổi.",
  "Cho tam giác ABC cân tại A. Đường cao AD, BE cắt nhau tại H. Gọi O là tâm đường tròn ngoại tiếp tam giác AHE. Chứng minh tứ giác ABDE nội tiếp.",
  "Cho nửa đường tròn (O) đường kính AB. Gọi C là một điểm trên nửa đường tròn. Kẻ CH vuông góc với AB. Gọi M và N lần lượt là hình chiếu của H trên AC và BC. Chứng minh tứ giác CMHN nội tiếp.",
  "Cho hình thoi ABCD có góc A = 60 độ. Gọi E, F lần lượt là trung điểm của AB và BC. Chứng minh tứ giác DEBF nội tiếp (hoặc các điểm liên quan).",
  "Cho tam giác ABC nội tiếp đường tròn (O). Phân giác trong của góc A cắt đường tròn tại D. Chứng minh tứ giác ABDC nội tiếp (hiển nhiên) và gọi I là tâm đường tròn nội tiếp, chứng minh tứ giác AIO... (bài toán mở rộng).",
  "Cho đường tròn (O) và điểm M ngoài đường tròn. Vẽ hai cát tuyến MAB và MCD. Chứng minh tứ giác ACDB nội tiếp.",
  "Cho tam giác ABC vuông tại A. Gọi M là trung điểm của AC. Đường tròn đường kính MC cắt BC tại N. BM cắt đường tròn tại I. Chứng minh tứ giác ABIN nội tiếp.",
  "Cho tứ giác ABCD nội tiếp đường tròn (O). Gọi E là giao điểm của AB và CD, F là giao điểm của AD và BC. Chứng minh các đường phân giác của góc E và góc F vuông góc với nhau tạo thành tứ giác nội tiếp nhỏ bên trong.",
  "Cho tam giác ABC. Đường tròn tâm I nội tiếp tam giác tiếp xúc với các cạnh BC, CA, AB lần lượt tại D, E, F. Chứng minh các tứ giác AEIF, BFID, CDIE nội tiếp.",
  "Cho tam giác ABC nhọn. Các đường cao AD, BE, CF. Gọi M, N, P, Q lần lượt là hình chiếu của D trên AB, AC, BE, CF. Chứng minh M, N, P, Q cùng thuộc một đường tròn.",
  "Cho đường tròn (O) đường kính AB. Dây cung CD vuông góc với AB tại H. Gọi M là một điểm trên cung nhỏ CB. AM cắt CD tại N. Chứng minh tứ giác HMNB nội tiếp.",
  "Cho hình chữ nhật ABCD. Kẻ BH vuông góc với AC. Gọi M, K lần lượt là trung điểm của AH và CD. Chứng minh tứ giác BMKC nội tiếp.",
  "Cho tam giác ABC vuông tại A. Đường cao AH. Gọi D, E là hình chiếu của H lên AB, AC. Chứng minh tứ giác ADHE nội tiếp và tứ giác BDEC nội tiếp.",
  "Cho đường tròn (O) và điểm A nằm ngoài. Kẻ tiếp tuyến AB và cát tuyến ACD. Tia phân giác góc BAC cắt BC, BD lần lượt tại M, N. Chứng minh tứ giác ABMN có tính chất nội tiếp đặc biệt.",
  "Cho tam giác ABC có ba góc nhọn. Các đường cao AD, BE, CF cắt nhau tại H. Gọi M là trung điểm của BC. Đường thẳng qua H vuông góc với HM cắt AB, AC tại P, Q. Chứng minh tứ giác APHQ nội tiếp.",
  "Cho tam giác ABC nhọn. Đường tròn đường kính AB cắt AC tại D. Đường tròn đường kính AC cắt AB tại E. Gọi H là giao điểm của BD và CE. Chứng minh tứ giác ADHE nội tiếp.",
  "Cho tam giác ABC cân tại A. Gọi M là trung điểm của BC. Kẻ MH vuông góc với AC. Gọi I là trung điểm của MH. Chứng minh tứ giác AIM... (bài toán hình học phẳng nâng cao về tứ giác nội tiếp).",
  "Cho hai đường tròn (O) và (O') tiếp xúc ngoài tại A. Kẻ tiếp tuyến chung ngoài BC (B thuộc O, C thuộc O'). Tiếp tuyến chung trong tại A cắt BC tại M. Chứng minh tứ giác OBCO' nội tiếp đường tròn đường kính OO'.",
  "Cho hình vuông ABCD. Gọi M, N lần lượt là trung điểm của BC và CD. AM và BN cắt nhau tại I. Chứng minh tứ giác ABID nội tiếp.",
  "Cho tam giác ABC. Gọi D, E, F lần lượt là chân các đường cao hạ từ A, B, C. Gọi M là trung điểm của BC. Chứng minh tứ giác MEFD nội tiếp.",
  "Cho đường tròn (O) đường kính AB. Điểm C thuộc (O). Gọi H là hình chiếu của C trên AB. Đường tròn đường kính CH cắt AC, BC tại D, E. Chứng minh tứ giác CDEH là hình chữ nhật và tứ giác ABED nội tiếp.",
  "Cho tam giác ABC vuông tại A. M là điểm bất kỳ trên cạnh AC. Đường tròn đường kính MC cắt BC tại D. BM cắt đường tròn tại I. Chứng minh tứ giác ABCI nội tiếp.",
  "Cho tam giác ABC nhọn. H là trực tâm. M là trung điểm BC. Đường thẳng qua H vuông góc với HM cắt AB, AC tại E, F. Chứng minh tứ giác EBCF nội tiếp.",
  "Cho đường tròn (O) và dây cung AB. Gọi M là điểm chính giữa cung nhỏ AB. C là điểm bất kỳ trên cung lớn AB. Dây MC cắt AB tại D. Chứng minh tứ giác MDO... (bài toán liên quan tứ giác nội tiếp).",
  "Cho tam giác ABC vuông tại A. Đường phân giác AD. Gọi E, F lần lượt là hình chiếu của D trên AB, AC. Chứng minh tứ giác AEDF nội tiếp và là hình vuông.",
  "Cho tam giác ABC nhọn. Các đường cao AD, BE, CF cắt nhau tại H. Gọi I là trung điểm của AH. Chứng minh tứ giác BFIE (hoặc tương tự) nội tiếp.",
  "Cho đường tròn (O) đường kính AB. C là điểm trên đường tròn. Tiếp tuyến tại C cắt AB tại D. Chứng minh tứ giác... (bài toán tiếp tuyến cơ bản).",
  "Cho hình bình hành ABCD. Đường tròn ngoại tiếp tam giác ABC cắt CD tại E. Chứng minh tứ giác ABED nội tiếp (hình thang cân).",
  "Cho tam giác ABC. Gọi I là tâm đường tròn nội tiếp. Đường thẳng vuông góc với CI tại I cắt AC, BC tại M, N. Chứng minh tứ giác... nội tiếp.",
  "Cho tam giác ABC vuông tại A. Gọi H là hình chiếu của A trên BC. Trên tia đối của tia HA lấy điểm D sao cho HD = HA. Chứng minh tứ giác ABDC nội tiếp.",
  "Cho đường tròn (O) và điểm M nằm ngoài. Kẻ hai tiếp tuyến MA, MB. Gọi H là giao điểm của MO và AB. Kẻ cát tuyến MCD. Chứng minh tứ giác OHCD nội tiếp.",
  "Cho tam giác ABC có góc A = 45 độ. Các đường cao BD, CE cắt nhau tại H. Chứng minh tứ giác ADHE nội tiếp và tứ giác BCDE nội tiếp.",
  "Cho đường tròn tâm O. Đường kính AB. Dây cung CD vuông góc với AB tại I (I nằm giữa A và O). Lấy điểm E trên cung nhỏ BC. AE cắt CD tại F. Chứng minh tứ giác BEFI nội tiếp.",
  "Cho tam giác ABC vuông tại A. M là trung điểm của AC. Đường tròn đường kính MC cắt BC tại N. Chứng minh tứ giác AMNB nội tiếp.",
  "Cho tam giác ABC đều. Lấy điểm M trên cạnh BC. Gọi D, E lần lượt là hình chiếu của M trên AB, AC. Chứng minh tứ giác ADME nội tiếp.",
  "Cho nửa đường tròn (O) đường kính AB. Lấy M thuộc OA. Qua M kẻ đường thẳng vuông góc với AB cắt nửa đường tròn tại C. Trên cung AC lấy điểm D. Tiếp tuyến tại D cắt đường thẳng CM tại E. Chứng minh tứ giác... nội tiếp.",
  "Cho tam giác ABC nội tiếp đường tròn (O). Tia phân giác góc A cắt BC tại D và cắt đường tròn tại E. Chứng minh... liên quan đến tứ giác nội tiếp.",
  "Cho hình thang vuông ABCD (vuông tại A và D). Gọi E là trung điểm của AD. Kẻ EC vuông góc với EB. Chứng minh tứ giác ABCD nội tiếp (hoặc các điểm liên quan).",
  "Cho tam giác ABC nhọn. Gọi O là tâm đường tròn ngoại tiếp. Gọi H là trực tâm. Chứng minh tứ giác... liên quan đến đường thẳng Euler nội tiếp.",
  "Cho đường tròn (O) đường kính AB. Gọi H là trung điểm của OA. Kẻ dây cung CD vuông góc với AB tại H. Lấy điểm E trên cung nhỏ AC. Chứng minh tứ giác... nội tiếp.",
  "Cho tam giác ABC vuông tại A. Đường cao AH. Gọi D là điểm đối xứng của A qua H. Chứng minh tứ giác ABDC nội tiếp.",
  "Cho hình vuông ABCD. E là điểm trên cạnh CD. Tia phân giác của góc DAE cắt CD tại F. Chứng minh... liên quan tứ giác nội tiếp.",
  "Cho tam giác ABC. Gọi M, N là trung điểm của AB, AC. Kẻ đường cao AH. Chứng minh tứ giác MNH... nội tiếp.",
  "Cho đường tròn (O). Từ điểm A ngoài đường tròn kẻ tiếp tuyến AB, AC. Gọi M là trung điểm của AC. BM cắt (O) tại N. Chứng minh tứ giác... nội tiếp.",
  "Cho đường tròn (O) đường kính AB. Dây cung CD vuông góc với AB tại H. Kẻ CK vuông góc với AD tại K. Chứng minh tứ giác AHKC nội tiếp.",
  "Cho tam giác MNP nhọn. Các đường cao MH, NK cắt nhau tại I. Chứng minh tứ giác NHIK nội tiếp.",
  "Cho hình vuông ABCD. Lấy điểm E trên cạnh AB, điểm F trên cạnh AD. Kẻ AH vuông góc với EF tại H. Chứng minh tứ giác AHFD nội tiếp.",
  "Cho đường tròn (O). Điểm S nằm ngoài đường tròn. Kẻ tiếp tuyến SA (A là tiếp điểm) và cát tuyến SBC (B nằm giữa S và C). Gọi I là trung điểm của dây BC. Chứng minh tứ giác SAOI nội tiếp.",
  "Cho tam giác ABC cân tại A. Đường cao AH. Kẻ HE vuông góc với AB tại E, HF vuông góc với AC tại F. Chứng minh tứ giác AEHF nội tiếp.",
  "Cho nửa đường tròn tâm O đường kính AB. Kẻ dây AC bất kỳ. Kẻ dây CD song song với AB (D thuộc nửa đường tròn). Chứng minh tứ giác ACDB nội tiếp.",
  "Cho tam giác ABC vuông tại A. Tia phân giác của góc B cắt cạnh AC tại D. Kẻ DE vuông góc với BC tại E. Chứng minh tứ giác ABED nội tiếp."
]

SYSTEM_PROMPT = "Bạn là chuyên gia trích xuất dữ liệu hình học từ đề bài tiếng Việt. Hãy phân tích đề bài và trả về JSON array mô tả các đối tượng (ENTITY), quan hệ (RELATION) và mục tiêu (GOAL)."

dataset = []
for prob in all_problems:
    dataset.append({
        "instruction": SYSTEM_PROMPT,
        "input": prob.strip(),
        "output": generate_synthetic_output(prob) 
    })

# Lưu file - Lúc này json.dump mới xử lý format
with open("geometry_finetune_clean.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"HOÀN TẤT! {len(dataset)} problems processed and saved to geometry_finetune_clean.json")