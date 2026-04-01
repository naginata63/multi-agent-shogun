#!/usr/bin/env node
"use strict";
/**
 * Shogun MCP Server - Phase 1 Experiment
 * Port: 3200 (本番3100と衝突回避)
 * Transport: stdio (MCP標準)
 *
 * 公開Tools:
 *   1. create_task
 *   2. get_assigned_tasks
 *   3. update_task_status
 *   4. send_message
 *   5. get_unread_messages
 *   6. submit_report
 */
Object.defineProperty(exports, "__esModule", { value: true });
const mcp_js_1 = require("@modelcontextprotocol/sdk/server/mcp.js");
const stdio_js_1 = require("@modelcontextprotocol/sdk/server/stdio.js");
const zod_1 = require("zod");
const database_js_1 = require("./database.js");
const server = new mcp_js_1.McpServer({
    name: "shogun-mcp-server",
    version: "1.0.0",
});
// ============================================================
// Tool 1: create_task
// ============================================================
server.tool("create_task", "タスクを作成してエージェントに割り当てる", {
    task_id: zod_1.z.string().describe("一意なタスクID (例: exp_001)"),
    assignee: zod_1.z.string().describe("担当エージェントID (例: ashigaru1-exp)"),
    description: zod_1.z.string().describe("タスクの内容"),
    parent_cmd: zod_1.z.string().optional().describe("親コマンドID (例: cmd_1068)"),
}, async ({ task_id, assignee, description, parent_cmd }) => {
    const result = (0, database_js_1.createTask)(task_id, assignee, description, parent_cmd ?? "");
    return {
        content: [
            { type: "text", text: JSON.stringify(result, null, 2) },
        ],
    };
});
// ============================================================
// Tool 2: get_assigned_tasks
// ============================================================
server.tool("get_assigned_tasks", "エージェントに割り当てられた未完了タスクを取得する", {
    agent_id: zod_1.z.string().describe("エージェントID (例: ashigaru1-exp)"),
}, async ({ agent_id }) => {
    const result = (0, database_js_1.getAssignedTasks)(agent_id);
    return {
        content: [
            { type: "text", text: JSON.stringify(result, null, 2) },
        ],
    };
});
// ============================================================
// Tool 3: update_task_status
// ============================================================
server.tool("update_task_status", "タスクのステータスを更新する", {
    task_id: zod_1.z.string().describe("タスクID"),
    status: zod_1.z
        .enum(["assigned", "in_progress", "done", "failed"])
        .describe("新しいステータス"),
}, async ({ task_id, status }) => {
    const result = (0, database_js_1.updateTaskStatus)(task_id, status);
    return {
        content: [
            { type: "text", text: JSON.stringify(result, null, 2) },
        ],
    };
});
// ============================================================
// Tool 4: send_message
// ============================================================
server.tool("send_message", "エージェント間メッセージを送信する (inbox代替)", {
    to: zod_1.z.string().describe("送信先エージェントID"),
    content: zod_1.z.string().describe("メッセージ内容"),
    type: zod_1.z
        .string()
        .optional()
        .describe("メッセージタイプ (task_assigned, report_done, etc.)"),
    from: zod_1.z.string().describe("送信元エージェントID"),
}, async ({ to, content, type, from }) => {
    const result = (0, database_js_1.sendMessage)(to, content, type ?? "message", from);
    return {
        content: [
            { type: "text", text: JSON.stringify(result, null, 2) },
        ],
    };
});
// ============================================================
// Tool 5: get_unread_messages
// ============================================================
server.tool("get_unread_messages", "未読メッセージを取得して既読にマークする", {
    agent_id: zod_1.z.string().describe("エージェントID"),
}, async ({ agent_id }) => {
    const result = (0, database_js_1.getUnreadMessages)(agent_id);
    return {
        content: [
            { type: "text", text: JSON.stringify(result, null, 2) },
        ],
    };
});
// ============================================================
// Tool 6: submit_report
// ============================================================
server.tool("submit_report", "タスク完了報告を提出する", {
    worker_id: zod_1.z.string().describe("担当エージェントID"),
    task_id: zod_1.z.string().describe("完了したタスクID"),
    result: zod_1.z.string().describe("完了内容・成果物の説明"),
}, async ({ worker_id, task_id, result }) => {
    const res = (0, database_js_1.submitReport)(worker_id, task_id, result);
    return {
        content: [
            { type: "text", text: JSON.stringify(res, null, 2) },
        ],
    };
});
// ============================================================
// Resource: stats (読取専用)
// ============================================================
server.resource("stats", "mcp://stats/current", async (uri) => {
    const stats = (0, database_js_1.getStats)();
    return {
        contents: [
            {
                uri: uri.href,
                mimeType: "application/json",
                text: JSON.stringify(stats, null, 2),
            },
        ],
    };
});
// ============================================================
// 起動
// ============================================================
async function main() {
    const transport = new stdio_js_1.StdioServerTransport();
    await server.connect(transport);
    process.stderr.write(`[MCP] shogun-mcp-server v1.0.0 起動完了 (stdio transport)\n`);
}
main().catch((err) => {
    process.stderr.write(`[MCP] 起動エラー: ${err}\n`);
    process.exit(1);
});
