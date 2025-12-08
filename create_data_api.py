import json
import time
import os
from tqdm import tqdm
import google.generativeai as genai
from dotenv import load_dotenv

# --- CẤU HÌNH ---
# Thay bằng API Key của bạn
# 1. CẤU HÌNH CLIENT (SDK MỚI)
load_dotenv()
key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=key)

# Dùng model Pro để có tư duy tốt nhất
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 0.0,
        "response_mime_type": "application/json"
    }
)

# --- DANH SÁCH ĐỀ BÀI (Mẫu) ---
# Bạn hãy copy toàn bộ danh sách 100 đề bài vào đây
problems = [
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

# --- PROMPT TỔNG QUÁT (MASTER PROMPT) ---
# Đây là "Bí kíp" để Thầy dạy Trò.
SYSTEM_PROMPT = """
Bạn là chuyên gia dữ liệu hình học phẳng. Nhiệm vụ: Phân tích đề bài và chuyển đổi sang JSON chuẩn để huấn luyện AI.

### 1. QUY TẮC QUAN TRỌNG
- **Trung thực:** Chỉ trích xuất thông tin có trong đề.
- **Suy luận ngữ cảnh:**
  - "Góc A=60" trong tam giác ABC -> `points: ["B", "A", "C"]`.
  - "Đường cao AH" -> `base` là cạnh đối diện (BC).
  - "Tiếp tuyến AB" -> `contact` là B (nếu B thuộc đường tròn).

### 2. JSON SCHEMA (CẤU TRÚC DỮ LIỆU)

#### A. HÌNH CƠ BẢN
- **Tam giác**: 
  `{"type": "TRIANGLE", "points": ["A", "B", "C"], "properties": [], "vertex": null}`
  - `properties`: List chứa `["RIGHT", "ISOSCELES", "EQUILATERAL", "ACUTE", "OBTUSE"]`.
  - `vertex`: Đỉnh đặc biệt (nếu có). VD: Vuông tại A -> `vertex: "A"`.
  
- **Tứ giác**: 
  `{"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"], "subtype": "SQUARE"|"RECTANGLE"|"RHOMBUS"|"TRAPEZOID"|"PARALLELOGRAM"|null}`

- **Đường tròn / Nửa đường tròn**: 
  `{"type": "CIRCLE", "center": "O", "diameter": ["A", "B"]}` 
  `{"type": "SEMICIRCLE", "center": "O", "diameter": ["A", "B"]}`

#### B. QUAN HỆ & ĐỐI TƯỢNG PHỤ
- **Giá trị (Góc/Cạnh)**: 
  `{"type": "VALUE", "subtype": "angle"|"length", "points": ["A", "B", "C"], "value": 60}`
- **Song song**: `{"type": "PARALLEL", "lines": [["A", "B"], ["C", "D"]]}`
- **Vuông góc**: `{"type": "PERPENDICULAR", "lines": [["A", "B"], ["C", "D"]]}`
- **Đường cao**: `{"type": "ALTITUDE", "top": "A", "foot": "H", "base": ["B", "C"]}`
- **Trung điểm**: `{"type": "MIDPOINT", "point": "M", "segment": ["A", "B"]}`
- **Giao điểm**: `{"type": "INTERSECTION", "point": "I", "lines": [["A", "B"], ["C", "D"]]}`
- **Tiếp tuyến**: `{"type": "TANGENT", "line": ["A", "x"], "contact": "A", "circle": "O"}`
- **Vị trí điểm**: `{"type": "POINT_LOCATION", "point": "A", "circle": "O", "location": "OUTSIDE"|"INSIDE"|"ON"}`
- **Thẳng hàng**: `{"type": "COLLINEAR", "points": ["A", "B", "C"]}`

#### C. MỤC TIÊU
- `{"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}` (Lấy từ câu hỏi chứng minh).

### 3. VÍ DỤ MINH HỌA (FEW-SHOT)

**Ví dụ 1 (Tam giác đặc biệt):** "Cho tam giác ABC vuông cân tại A. Đường cao AH."
**Output:**
[
  {
    "type": "TRIANGLE", 
    "points": ["A", "B", "C"], 
    "properties": ["RIGHT", "ISOSCELES"], 
    "vertex": "A"
  },
  {
    "type": "ALTITUDE", 
    "top": "A", "foot": "H", "base": ["B", "C"]
  }
]

**Ví dụ 2 (Đường tròn & Tiếp tuyến):** "Cho đường tròn (O). Từ điểm A nằm ngoài, kẻ tiếp tuyến AB (B là tiếp điểm)."
**Output:**
[
  {"type": "CIRCLE", "center": "O"},
  {"type": "POINT_LOCATION", "point": "A", "circle": "O", "location": "OUTSIDE"},
  {"type": "TANGENT", "line": ["A", "B"], "contact": "B", "circle": "O"}
]

**Ví dụ 3 (Tứ giác nội tiếp):** "Cho tứ giác ABCD. Góc D = 60 độ. Chứng minh tứ giác ABCD nội tiếp."
**Output:**
[
  {"type": "QUADRILATERAL", "points": ["A", "B", "C", "D"]},
  {"type": "VALUE", "subtype": "angle", "points": ["A", "D", "C"], "value": 60},
  {"type": "RENDER_ORDER", "points": ["A", "B", "C", "D"]}
]
"""

# --- HÀM SINH DỮ LIỆU ---
def create_dataset():
    dataset = []
    print(f"🚀 Đang xử lý {len(problems)} đề bài bằng Gemini Pro...")
    
    for i, prob in enumerate(tqdm(problems)):
        try:
            # Gửi request
            response = model.generate_content(f"{SYSTEM_PROMPT}\n\nĐỀ BÀI: {prob}")
            json_label = json.loads(response.text)
            
            # Tạo mẫu training chuẩn
            entry = {
                "instruction": "Trích xuất các thực thể và quan hệ hình học từ đề bài sau thành JSON.",
                "input": prob,
                "output": json_label 
            }
            dataset.append(entry)
            
            # Nghỉ xíu để tránh Rate Limit
            time.sleep(2)
            
        except Exception as e:
            print(f"\n❌ Lỗi bài {i+1}: {e}")
            # Thử lại hoặc bỏ qua
            continue

    # Lưu file
    with open("finetune_dataset_gold.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Đã tạo xong file 'finetune_dataset_gold.json' chất lượng cao!")

if __name__ == "__main__":
    create_dataset()