"use client";

import React, { useCallback, useMemo, useState, useTransition } from "react";
import { Card, Col, DatePicker, Divider, Empty, Flex, Row, Segmented, Select, Space, Spin, Statistic, Typography, message } from "antd";
import { Line, Column } from "@ant-design/plots";
import dayjs, { Dayjs } from "dayjs";
import { LoadingOutlined } from "@ant-design/icons";
import usePrStatsDashboardStyles from "./style";
import { fetchPrStatsAction } from "../../actions";

const { RangePicker } = DatePicker;

type BucketOption = "day" | "week" | "month";

type PrStatsBucket = {
  bucket_start: string;
  bucket_end: string;
  label: string;
};

type PrStatsMetric = {
  created: number;
  merged: number;
  closed: number;
};

type PrStatsAuthor = {
  author: string;
  series: PrStatsMetric[];
  totals: PrStatsMetric;
};

type PrStatsResponse = {
  repo: string;
  bucket: BucketOption;
  buckets: PrStatsBucket[];
  authors: PrStatsAuthor[];
  totals: PrStatsMetric;
};

type PrStatsDashboardProps = {
  owner: string;
  project: string;
  initialData: PrStatsResponse | null;
  initialBucket: BucketOption;
  initialSince: string;
  initialUntil: string;
  initialAuthor?: string | null;
};

const metricLabels: Record<keyof PrStatsMetric, string> = {
  created: "创建",
  merged: "合并",
  closed: "关闭",
};

const metricFields: Array<keyof PrStatsMetric> = ["created", "merged", "closed"];

export default function PrStatsDashboard({
  owner,
  project,
  initialData,
  initialBucket,
  initialSince,
  initialUntil,
  initialAuthor = null,
}: PrStatsDashboardProps) {
  const [bucket, setBucket] = useState<BucketOption>(initialBucket);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs(initialSince),
    dayjs(initialUntil),
  ]);
  const [selectedMetric, setSelectedMetric] = useState<keyof PrStatsMetric>("created");
  const [selectedAuthor, setSelectedAuthor] = useState<string | null>(initialAuthor ?? null);
  const [data, setData] = useState<PrStatsResponse | null>(initialData);
  const [pending, startTransition] = useTransition();
  const {
    styles: { layout, toolbar, filterGroup, chartCard, chartWrapper, legend, emptyWrapper },
  } = usePrStatsDashboardStyles();

  const refreshData = useCallback(
    (nextBucket: BucketOption, nextRange: [Dayjs, Dayjs], nextAuthor: string | null) => {
      const sinceIso = nextRange[0]?.startOf("day").toISOString();
      const untilIso = nextRange[1]?.endOf("day").toISOString();

      if (!sinceIso || !untilIso) {
        return;
      }

      startTransition(async () => {
        try {
          const response = await fetchPrStatsAction({
            owner,
            project,
            bucket: nextBucket,
            since: sinceIso,
            until: untilIso,
            author: nextAuthor ?? undefined,
          });
          setData(response);
        } catch (error) {
          const messageText = error instanceof Error ? error.message : "PR 统计数据获取失败";
          message.error(messageText);
        }
      });
    },
    [owner, project],
  );

  const aggregatedTimeline = useMemo(() => {
    if (!data) return [];
    return data.buckets.map((bucketMeta, idx) => {
      const counts = data.authors.reduce(
        (acc, author) => {
          const cell = author.series[idx];
          if (!cell) return acc;
          acc.created += cell.created;
          acc.merged += cell.merged;
          acc.closed += cell.closed;
          return acc;
        },
        { created: 0, merged: 0, closed: 0 }
      );
      return {
        label: bucketMeta.label,
        ...counts,
      };
    });
  }, [data]);

  const lineChartData = useMemo(() => {
    return aggregatedTimeline.flatMap((bucketPoint) =>
      metricFields.map((metric) => ({
        bucket: bucketPoint.label,
        type: metricLabels[metric],
        count: bucketPoint[metric],
      }))
    );
  }, [aggregatedTimeline]);

  const columnChartData = useMemo(() => {
    if (!data) return [];
    return data.authors.flatMap((author) =>
      data.buckets.map((bucketMeta, idx) => ({
        bucket: bucketMeta.label,
        author: author.author ?? "unknown",
        value: author.series[idx]?.[selectedMetric] ?? 0,
      }))
    );
  }, [data, selectedMetric]);

  const authorOptions = useMemo(() => {
    if (!data) return [];
    return data.authors.map((author) => ({
      label: author.author,
      value: author.author,
    }));
  }, [data]);

  const totalsDisplay = useMemo(() => {
    if (!data) return null;
    return (
      <Row gutter={16}>
        {metricFields.map((metric) => (
          <Col xs={24} sm={8} key={metric}>
            <Statistic
              title={`${metricLabels[metric]}总数`}
              value={data.totals[metric]}
              valueStyle={{ fontWeight: 600 }}
            />
          </Col>
        ))}
      </Row>
    );
  }, [data]);

  const renderCharts = () => {
    if (!data || data.buckets.length === 0) {
      return (
        <Flex align="center" justify="center" className={emptyWrapper}>
          <Empty description="暂无统计数据" />
        </Flex>
      );
    }

    return (
      <Space direction="vertical" size={16} className={chartWrapper}>
        <Card size="small" className={chartCard} title="时间趋势">
          <Line
            data={lineChartData}
            xField="bucket"
            yField="count"
            seriesField="type"
            smooth
            tooltip={{ showMarkers: true }}
            point={{
              shape: "circle",
              size: 4,
            }}
            legend={{ position: "top" }}
            animation={false}
          />
        </Card>
        <Card
          size="small"
          className={chartCard}
          title={
            <Flex justify="space-between" align="center">
              <Typography.Text strong>作者分布</Typography.Text>
              <Segmented
                size="small"
                options={metricFields.map((metric) => ({
                  label: metricLabels[metric],
                  value: metric,
                }))}
                value={selectedMetric}
                onChange={(val) => setSelectedMetric(val as keyof PrStatsMetric)}
              />
            </Flex>
          }
        >
          <Column
            data={columnChartData}
            isStack
            xField="bucket"
            yField="value"
            seriesField="author"
            legend={{
              position: "top",
              maxRow: 2,
              itemName: {
                style: {
                  fontSize: 12,
                },
              },
            }}
            tooltip={{
              shared: true,
            }}
            interactions={[{ type: "active-region" }]}
            animation={false}
          />
        </Card>
        <Card size="small" className={chartCard} title="作者总览">
          <Flex gap={12} className={legend} wrap>
            {data.authors.map((author) => (
              <Flex key={author.author} justify="space-between" align="center" wrap>
                <Typography.Text>{author.author}</Typography.Text>
                <Space size={24}>
                  {metricFields.map((metric) => (
                    <Typography.Text key={metric} type="secondary">
                      {metricLabels[metric]}：{author.totals[metric]}
                    </Typography.Text>
                  ))}
                </Space>
              </Flex>
            ))}
          </Flex>
        </Card>
      </Space>
    );
  };

  return (
    <Flex vertical gap={16} className={layout}>
      <Card>
        <Flex className={toolbar} justify="space-between" align="center" wrap>
          <Space size={16} direction="horizontal" className={filterGroup} wrap>
            <Typography.Text type="secondary">时间粒度</Typography.Text>
            <Segmented<BucketOption>
              options={[
                { label: "按日", value: "day" },
                { label: "按周", value: "week" },
                { label: "按月", value: "month" },
              ]}
              value={bucket}
              onChange={(value) => {
                const nextBucket = value as BucketOption;
                setBucket(nextBucket);
                refreshData(nextBucket, dateRange, selectedAuthor);
              }}
            />
            <Divider type="vertical" />
            <Typography.Text type="secondary">时间范围</Typography.Text>
            <RangePicker
              value={dateRange}
              onChange={(range) => {
                if (!range || !range[0] || !range[1]) return;
                const nextRange: [Dayjs, Dayjs] = [range[0], range[1]];
                setDateRange(nextRange);
                refreshData(bucket, nextRange, selectedAuthor);
              }}
              presets={[
                { label: "近7天", value: [dayjs().subtract(6, "day"), dayjs()] },
                { label: "近30天", value: [dayjs().subtract(29, "day"), dayjs()] },
                { label: "近90天", value: [dayjs().subtract(89, "day"), dayjs()] },
              ]}
              disabledDate={(current) => current && current > dayjs().endOf("day")}
            />
            <Divider type="vertical" />
            <Typography.Text type="secondary">作者</Typography.Text>
            <Select
              allowClear
              placeholder="全部作者"
              style={{ minWidth: 160 }}
              options={authorOptions}
              value={selectedAuthor ?? undefined}
              onChange={(value) => {
                const nextAuthor = value ?? null;
                setSelectedAuthor(nextAuthor);
                refreshData(bucket, dateRange, nextAuthor);
              }}
            />
          </Space>
          {(pending) && <Spin indicator={<LoadingOutlined spin />} />}
        </Flex>
        <Divider style={{ margin: "12px 0" }} />
        {totalsDisplay}
      </Card>
      {renderCharts()}
    </Flex>
  );
}

