"use client";

import React from "react";
import { Layout,  theme, Breadcrumb, Drawer, Button } from "antd";
import Sidebar from "./Sidebar";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { MenuOutlined } from "@ant-design/icons";

const {  Content, Header, Footer } = Layout;

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const {
    token: {  borderRadiusLG,colorPrimary },
  } = theme.useToken();

  const breadcrumbItems = pathname
    .split("/")
    .filter(Boolean)
    .map((segment) => ({ title: segment }));

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Layout>
        <Header
          style={{ background: "#f6f8fa",paddingTop:'16px',paddingLeft:'0px' }}
          className="sticky top-0 z-[1] w-full flex items-center align-center"
        >
          <div className="flex items-center gap-2 w-full">
            <Button
              type="text"
              aria-label="打开菜单"
              icon={<MenuOutlined />}
              onClick={() => setMenuOpen(true)}
              style={{ marginLeft: 8 }}
            />
            <Breadcrumb  items={breadcrumbItems} />
          </div>
        </Header>
        <Drawer
          title="菜单"
          placement="left"
          width={260}
          open={menuOpen}
          onClose={() => setMenuOpen(false)}
        >
          <Sidebar onNavigate={() => setMenuOpen(false)} />
        </Drawer>
        <Content style={{ background: "#fff", padding: "16px 16px",position:'relative' }}>
            {children}
        </Content>
        <Footer style={{ textAlign: "center", background: "#fff" }}>AI Review ©{new Date().getFullYear()}</Footer>
      </Layout>
    </Layout>
  );
}


