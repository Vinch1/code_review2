"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { MenuProps } from "antd";
import { Menu } from "antd";
import {
  AppstoreOutlined,
  SwapOutlined,
} from "@ant-design/icons";

function getSelectedKey(pathname: string): string {
  if (pathname.startsWith("/projects")) return "/projects";
  if (pathname.startsWith("/monitor")) return "/monitor";
  if (pathname.startsWith("/signin")) return "/signin";
  if (pathname.startsWith("/redirect")) return "/redirect";
  return "/";
}

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const selectedKey = getSelectedKey(pathname);

  const items = useMemo<MenuProps["items"]>(() => {
    return [
      {
        key: "/",
        icon: <AppstoreOutlined />,
        label: <Link href="/">项目</Link>,
      },
      {
        key: "/monitor",
        icon: <SwapOutlined />,
        label: <Link href="/monitor">监控</Link>,
      },

    ];
  }, []);

  const handleClick: MenuProps["onClick"] = () => {
    if (onNavigate) onNavigate();
  };

  return (
    <Menu
      mode="inline"
      onClick={handleClick}
      selectedKeys={[selectedKey]}
      items={items}
      style={{ height: "100%", borderInlineEnd: 0 }}
    />
  );
}


