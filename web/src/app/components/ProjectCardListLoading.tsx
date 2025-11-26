import { Row, Col, Card, Flex, Skeleton } from "antd";
import SkeletonInput from "antd/es/skeleton/Input";
export default function ProjectCardListLoading() {
  const placeholderCards = Array.from({ length: 6 });
  return (
    <div className="w-full">
      <Row
        gutter={[16, 16]}
        className="w-full mt-6"
        style={{ alignSelf: "stretch" }}
        justify="start"
      >
        {placeholderCards.map((_, idx) => (
          <Col key={idx} span={8}>
            <Card
              hoverable
              title={
                <Flex align="center" justify="space-between" className="w-full">
                  <SkeletonInput active style={{ width: "50%", height: 24 }} />
                  <SkeletonInput active style={{ width: 120, height: 24 }} />
                </Flex>
              }
              style={{ height: "200px" }}
            >
              <Flex vertical gap={8} justify="space-between" style={{ height: "100px" }}>
                <Skeleton active paragraph={{ rows: 3 }} title={false} />
                <SkeletonInput active style={{ width: 180, height: 20 }} />
              </Flex>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}


