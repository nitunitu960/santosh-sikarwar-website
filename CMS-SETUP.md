# प्रबंधन पैनल सेटअप / Admin Panel Setup

आपकी वेबसाइट में एक प्रबंधन पैनल (Admin Panel) जोड़ा गया है। इससे आप बिना
कोडिंग के, एक लॉगिन पेज से समाचार, फ़ोटो और संपर्क जानकारी अपडेट कर सकते हैं।

पैनल का पता: **https://santoshsikarwar.in/admin/**

पैनल इस्तेमाल करने से पहले एक बार लॉगिन (OAuth) सेटअप करना होता है।
यह लगभग 10 मिनट का काम है और इसके लिए आपके GitHub खाते की ज़रूरत होगी।

---

## चरण 1 — GitHub OAuth App बनाएँ
1. GitHub में जाएँ: **Settings → Developer settings → OAuth Apps → New OAuth App**
2. भरें:
   - Application name: `Santosh Sikarwar CMS`
   - Homepage URL: `https://santoshsikarwar.in`
   - Authorization callback URL: (चरण 2 में मिलने वाला Worker URL) + `/callback`
3. **Register application** दबाएँ।
4. **Client ID** कॉपी करें और एक **Client Secret** बनाकर कॉपी करें।
   (इन्हें किसी को न दें — ये गोपनीय हैं।)

## चरण 2 — लॉगिन सर्वर (Cloudflare Worker) लगाएँ
Decap CMS को GitHub से जोड़ने के लिए एक छोटा मुफ़्त लॉगिन सर्वर चाहिए।
सबसे आसान: Cloudflare Worker (मुफ़्त, क्रेडिट कार्ड नहीं चाहिए)।

- एक तैयार समाधान: https://github.com/sterlingwes/decap-proxy
- Cloudflare खाता बनाएँ → Worker बनाएँ → ऊपर वाला कोड डालें →
  Client ID और Client Secret (चरण 1 वाले) Worker की settings में डालें → Deploy करें।
- Deploy के बाद जो Worker URL मिले (जैसे `https://xxxx.workers.dev`) उसे नोट करें।
- चरण 1 के callback URL में यही URL + `/callback` डालें।

## चरण 3 — config.yml अपडेट करें
फ़ाइल `admin/config.yml` में:
- `repo: YOUR-USERNAME/santosh-sikarwar-website` → अपना GitHub यूज़रनेम डालें
- `base_url: https://YOUR-OAUTH-URL` → चरण 2 वाला Worker URL डालें

फिर बदलाव push करें (या GitHub पर सीधे edit करें)।

## चरण 4 — पैनल इस्तेमाल करें
1. ब्राउज़र में खोलें: `https://santoshsikarwar.in/admin/`
2. **Login with GitHub** दबाएँ → अपने GitHub से लॉगिन करें।
3. अब आप देखेंगे:
   - **समाचार / गतिविधियाँ** — नई पोस्ट जोड़ें (तारीख, शीर्षक, विवरण, फ़ोटो)
   - **फोटो गैलरी** — फ़ोटो जोड़ें (drag & drop)
   - **प्रोफ़ाइल एवं संपर्क** — मुख्य फ़ोटो, ई-मेल, फ़ोन, क्षेत्र बदलें
4. **Publish** दबाते ही बदलाव अपने आप वेबसाइट पर आ जाएँगे (1–2 मिनट में)।

---

## अगर पैनल सेटअप जटिल लगे
कोई बात नहीं — बिना पैनल के भी आप वेबसाइट अपडेट कर सकते हैं।
`UPDATE-GUIDE.md` में GitHub से सीधे फ़ोटो/समाचार जोड़ने का आसान तरीका दिया है।

इनमें से किसी भी चरण में सहायता चाहिए तो मुझे बताएँ, मैं साथ में कर दूँगा।
