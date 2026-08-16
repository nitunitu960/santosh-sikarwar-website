/*
  ============================================================
  Decap CMS — GitHub Login Helper (Cloudflare Worker)
  ============================================================
  इस पूरे कोड को Cloudflare Worker में पेस्ट करें।
  फिर Worker की Settings में दो Variable जोड़ें:
    GITHUB_CLIENT_ID      = (GitHub OAuth App का Client ID)
    GITHUB_CLIENT_SECRET  = (GitHub OAuth App का Client Secret)
  ============================================================
*/

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname, searchParams } = url;

    const CLIENT_ID = env.GITHUB_CLIENT_ID;
    const CLIENT_SECRET = env.GITHUB_CLIENT_SECRET;

    // Step 1: begin login -> send user to GitHub
    if (pathname === "/auth") {
      const redirectUri = `${url.origin}/callback`;
      const scope = searchParams.get("scope") || "repo";
      const state = crypto.randomUUID();
      const authUrl =
        "https://github.com/login/oauth/authorize" +
        `?client_id=${CLIENT_ID}` +
        `&redirect_uri=${encodeURIComponent(redirectUri)}` +
        `&scope=${encodeURIComponent(scope)}` +
        `&state=${state}`;
      return Response.redirect(authUrl, 302);
    }

    // Step 2: GitHub returns here with a code -> swap it for a token
    if (pathname === "/callback") {
      const code = searchParams.get("code");
      if (!code) return new Response("Missing code", { status: 400 });

      const tokenRes = await fetch(
        "https://github.com/login/oauth/access_token",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            "User-Agent": "decap-cms-oauth",
          },
          body: JSON.stringify({
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            code,
          }),
        }
      );

      const data = await tokenRes.json();
      const provider = "github";
      const result = data.access_token
        ? `authorization:${provider}:success:${JSON.stringify({
            token: data.access_token,
            provider,
          })}`
        : `authorization:${provider}:error:${JSON.stringify(data)}`;

      const html =
        "<!doctype html><html><body><script>" +
        "(function(){" +
        "function receiveMessage(e){" +
        "window.opener.postMessage(" +
        JSON.stringify(result) +
        ", e.origin);" +
        "window.removeEventListener('message', receiveMessage, false);" +
        "}" +
        "window.addEventListener('message', receiveMessage, false);" +
        "window.opener.postMessage('authorizing:" +
        provider +
        "', '*');" +
        "})();" +
        "</script></body></html>";

      return new Response(html, {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    return new Response(
      "Decap CMS GitHub OAuth helper is running. Login starts at /auth",
      { headers: { "Content-Type": "text/plain" } }
    );
  },
};
