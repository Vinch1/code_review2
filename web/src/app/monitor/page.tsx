"use client";

import React, { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Card, Flex, Space, Tag, Typography, Select } from "antd";
import { useRouter, useSearchParams } from "next/navigation";

type StatusEvent = { line: string };
type LogEvent = { line: string };

export default function MonitorPage() {
  return (
    <Suspense fallback={null}>
      <MonitorContent />
    </Suspense>
  );
}

function MonitorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // 1️⃣ 初始值来自 URL 参数
  const initialService = searchParams.get("service") || "nginx";
  const [service, setService] = useState<string>(initialService);

  const [connected, setConnected] = useState<boolean>(false);
  const [statusLines, setStatusLines] = useState<string[]>([]);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (!service) return;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setConnected(false);
    setError(null);
    setStatusLines([]);
    setLogLines([]);

    const url = `/api/nextjs/monitor?service=${encodeURIComponent(service)}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("open", () => setConnected(true));
    es.addEventListener("status", (evt: MessageEvent) => {
      try {
        const data = JSON.parse(evt.data) as StatusEvent;
        if (data?.line) setStatusLines((prev) => [...prev, data.line]);
      } catch {}
    });
    es.addEventListener("log", (evt: MessageEvent) => {
      try {
        const data = JSON.parse(evt.data) as LogEvent;
        if (data?.line) setLogLines((prev) => [...prev, data.line].slice(-1000));
      } catch {}
    });
    es.addEventListener("error", (evt: MessageEvent) => {
      try {
        const data = JSON.parse(evt.data) as { message?: string };
        if (data?.message) setError(data.message);
      } catch {
        setError("连接发生错误");
      }
    });
    es.onerror = () => setConnected(false);
  }, [service]);

  // 2️⃣ 当 service 改变时，同步到 URL（不刷新页面）
  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("service", service);
    router.replace(`?${params.toString()}`);
  }, [service, router, searchParams]);

  // 3️⃣ 初次渲染时自动连接
  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect]);

  const connectionTag = useMemo(() => {
    if (error) return <Tag color="error">错误</Tag>;
    return connected ? <Tag color="success">已连接</Tag> : <Tag>未连接</Tag>;
  }, [connected, error]);

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        服务监控
      </Typography.Title>
      <Card>
        <Flex gap={8} align="center" wrap>
          <span>Service:</span>
          <Select
            style={{ width: 280 }}
            value={service}
            onChange={(val) => setService(val)} // 触发 URL 更新
            options={[
              { value: "nginx", label: "nginx" },
              { value: "flask", label: "flask" },
            ]}
          />
          <Button type="primary" onClick={connect}>
            连接
          </Button>
          {connectionTag}
        </Flex>
      </Card>

      <Flex gap={16} vertical>
        <Card title="Status">
          <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
            {statusLines.length ? statusLines.join("\n") : "(无)"}
          </pre>
        </Card>

        <Card title="Logs">
          <pre style={{ whiteSpace: "pre-wrap", margin: 0, maxHeight: 480, overflow: "auto" }}>
            {logLines.length ? logLines.join("\n") : "(无)"}
          </pre>
        </Card>
      </Flex>
    </Space>
  );
}
