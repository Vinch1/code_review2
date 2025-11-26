"use client";
import { Row, Col, Card, Flex, Skeleton } from "antd";

export default function Loading() {
  const placeholderCards = Array.from({ length: 6 });
  return (
    <div className="font-sans flex justify-center min-h-screen">
      <div className="flex flex-col gap-16 row-start-2 items-center sm:items-start w-full max-w-6xl mt-16">
        <Flex vertical gap={8} className="w-full">
          <Skeleton.Input active style={{ width: 200, height: 32 }} />
          <Skeleton.Input active style={{ width: 120, height: 20 }} />
        </Flex>

        <Row
          gutter={[16, 16]}
          className="w-full"
          style={{ alignSelf: "stretch" }}
          justify="start"
        >
          {placeholderCards.map((_, idx) => (
            <Col key={idx} span={8}>
              <Card
                hoverable
                title={
                  <Flex align="center" justify="space-between" className="w-full">
                    <Skeleton.Input active style={{ width: "50%", height: 24 }} />
                    <Skeleton.Input active style={{ width: 120, height: 24 }} />
                  </Flex>
                }
                style={{ height: "200px" }}
              >
                <Flex vertical gap={8} justify="space-between" style={{ height: "100px" }}>
                  <Skeleton active paragraph={{ rows: 3 }} title={false} />
                  <Skeleton.Input active style={{ width: 180, height: 20 }} />
                </Flex>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
}

