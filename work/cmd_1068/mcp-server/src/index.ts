#!/usr/bin/env node
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

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  createTask,
  getAssignedTasks,
  updateTaskStatus,
  sendMessage,
  getUnreadMessages,
  submitReport,
  getStats,
  updateAgentStatus,
  getAllAgentStatuses,
  getReports,
  saveAgentState,
  getAgentState,
  getDashboard,
  clearAllData,
} from "./database.js";

const server = new McpServer({
  name: "shogun-mcp-server",
  version: "1.0.0",
});

// ============================================================
// Tool 1: create_task
// ============================================================
server.tool(
  "create_task",
  "タスクを作成してエージェントに割り当てる",
  {
    task_id: z.string().describe("一意なタスクID (例: exp_001)"),
    assignee: z.string().describe("担当エージェントID (例: ashigaru1-exp)"),
    description: z.string().describe("タスクの内容"),
    parent_cmd: z.string().optional().describe("親コマンドID (例: cmd_1068)"),
  },
  async ({ task_id, assignee, description, parent_cmd }) => {
    const result = createTask(task_id, assignee, description, parent_cmd ?? "");
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 2: get_assigned_tasks
// ============================================================
server.tool(
  "get_assigned_tasks",
  "エージェントに割り当てられた未完了タスクを取得する",
  {
    agent_id: z.string().describe("エージェントID (例: ashigaru1-exp)"),
  },
  async ({ agent_id }) => {
    const result = getAssignedTasks(agent_id);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 3: update_task_status
// ============================================================
server.tool(
  "update_task_status",
  "タスクのステータスを更新する",
  {
    task_id: z.string().describe("タスクID"),
    status: z
      .enum(["assigned", "in_progress", "done", "failed"])
      .describe("新しいステータス"),
  },
  async ({ task_id, status }) => {
    const result = updateTaskStatus(task_id, status);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 4: send_message
// ============================================================
server.tool(
  "send_message",
  "エージェント間メッセージを送信する (inbox代替)",
  {
    to: z.string().describe("送信先エージェントID"),
    content: z.string().describe("メッセージ内容"),
    type: z
      .string()
      .optional()
      .describe("メッセージタイプ (task_assigned, report_done, etc.)"),
    from: z.string().describe("送信元エージェントID"),
  },
  async ({ to, content, type, from }) => {
    const result = sendMessage(to, content, type ?? "message", from);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 5: get_unread_messages
// ============================================================
server.tool(
  "get_unread_messages",
  "未読メッセージを取得して既読にマークする",
  {
    agent_id: z.string().describe("エージェントID"),
  },
  async ({ agent_id }) => {
    const result = getUnreadMessages(agent_id);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 6: submit_report
// ============================================================
server.tool(
  "submit_report",
  "タスク完了報告を提出する",
  {
    worker_id: z.string().describe("担当エージェントID"),
    task_id: z.string().describe("完了したタスクID"),
    result: z.string().describe("完了内容・成果物の説明"),
  },
  async ({ worker_id, task_id, result }) => {
    const res = submitReport(worker_id, task_id, result);
    return {
      content: [
        { type: "text", text: JSON.stringify(res, null, 2) },
      ],
    };
  }
);

// ============================================================
// Resource: stats (読取専用)
// ============================================================
server.resource(
  "stats",
  "mcp://stats/current",
  async (uri) => {
    const stats = getStats();
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(stats, null, 2),
        },
      ],
    };
  }
);

// ============================================================
// Resource: dashboard (Phase 2)
// ============================================================
server.resource(
  "dashboard",
  "mcp://dashboard/current",
  async (uri) => {
    const dashboard = getDashboard();
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(dashboard, null, 2),
        },
      ],
    };
  }
);

// ============================================================
// Tool 7: update_agent_status (Phase 2)
// ============================================================
server.tool(
  "update_agent_status",
  "エージェントのステータスを更新する",
  {
    agent_id: z.string().describe("エージェントID"),
    status: z
      .enum(["idle", "busy", "error", "offline"])
      .describe("新しいステータス"),
    current_task: z
      .string()
      .optional()
      .describe("現在のタスクID（任意）"),
  },
  async ({ agent_id, status, current_task }) => {
    const result = updateAgentStatus(agent_id, status, current_task);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 8: get_all_agent_statuses (Phase 2)
// ============================================================
server.tool(
  "get_all_agent_statuses",
  "全エージェントのステータスを取得する",
  {},
  async () => {
    const result = getAllAgentStatuses();
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 9: get_reports (Phase 2)
// ============================================================
server.tool(
  "get_reports",
  "完了報告を取得する（parent_cmdでフィルタ可）",
  {
    parent_cmd: z
      .string()
      .optional()
      .describe("親コマンドID（省略時は全件）"),
  },
  async ({ parent_cmd }) => {
    const result = getReports(parent_cmd);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 10: save_agent_state (Phase 2)
// ============================================================
server.tool(
  "save_agent_state",
  "エージェントの状態を保存する（コンパクション復旧用）",
  {
    agent_id: z.string().describe("エージェントID"),
    key: z.string().describe("状態キー（例: current_task_id, last_inbox_id）"),
    value: z.string().describe("状態値"),
  },
  async ({ agent_id, key, value }) => {
    const result = saveAgentState(agent_id, key, value);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 11: get_agent_state (Phase 2)
// ============================================================
server.tool(
  "get_agent_state",
  "エージェントの保存状態を取得する（コンパクション復旧用）",
  {
    agent_id: z.string().describe("エージェントID"),
  },
  async ({ agent_id }) => {
    const result = getAgentState(agent_id);
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// Tool 12: clear_all_data (Phase 2 test utility)
// ============================================================
server.tool(
  "clear_all_data",
  "全データをクリアする（テスト用）",
  {},
  async () => {
    const result = clearAllData();
    return {
      content: [
        { type: "text", text: JSON.stringify(result, null, 2) },
      ],
    };
  }
);

// ============================================================
// 起動
// ============================================================
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write(
    `[MCP] shogun-mcp-server v1.0.0 起動完了 (stdio transport)\n`
  );
}

main().catch((err) => {
  process.stderr.write(`[MCP] 起動エラー: ${err}\n`);
  process.exit(1);
});
