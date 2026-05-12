/**
 * Cloudflare Workers Cron Trigger
 * 每天 UTC 1:00（北京时间 9:00 ± 1分钟）准时触发 GitHub Actions
 *
 * 部署步骤（5分钟）：
 * 1. 注册/登录 cloudflare.com
 * 2. 左侧 Workers & Pages → Create Worker → Starter
 * 3. 把这段代码粘贴进去 → Deploy
 * 4. 创建 GitHub Token：github.com → Settings → Developer settings →
 *    Personal access tokens → Tokens (classic) → Generate new token →
 *    勾选 workflow 权限 → 复制 token
 * 5. Worker Settings → Variables → Encrypted Variables →
 *    添加 GITHUB_TOKEN = <你的token> ，GITHUB_USER = Jaffefan ，GITHUB_REPO = fan01--studio
 * 6. Worker Settings → Triggers → Add Cron Trigger →
 *    Cron pattern: 0 1 * * * （UTC 1:00 = 北京 9:00）
 *
 * 免费额度：10万次/天，我们只用 1 次/天，完全免费。
 */

export default {
  async scheduled(event, env, ctx) {
    const user = env.GITHUB_USER || "Jaffefan";
    const repo = env.GITHUB_REPO || "fan01--studio";
    const token = env.GITHUB_TOKEN;

    if (!token) {
      console.error("GITHUB_TOKEN not set in Worker secrets");
      return;
    }

    const url = `https://api.github.com/repos/${user}/${repo}/actions/workflows/daily.yml/dispatches`;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main" }),
    });

    const body = await resp.text();
    console.log(
      `[${new Date().toISOString()}] Triggered workflow: HTTP ${resp.status} — ${body}`
    );
  },

  // 可选：手工打 curl 也能触发（不依赖 cron）
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/trigger") {
      await this.scheduled(null, env, null);
      return new Response("OK — workflow triggered", { status: 200 });
    }
    return new Response("IAN podcast trigger is running.", { status: 200 });
  },
};
