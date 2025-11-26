import { createStyles } from "antd-style";

const usePrStatsDashboardStyles = createStyles(({ token, css }) => ({
  layout: css`
    width: 100%;
  `,
  toolbar: css`
    gap: 12px;
  `,
  filterGroup: css`
    display: flex;
    align-items: center;
  `,
  chartWrapper: css`
    width: 100%;
  `,
  chartCard: css`
    width: 100%;

    .ant-card-body {
      padding: 16px;
    }
  `,
  legend: css`
    width: 100%;
    gap: 12px;

    @media (max-width: 768px) {
      flex-direction: column;
      gap: 16px;
    }
  `,
  emptyWrapper: css`
    height: 280px;
    background: ${token.colorBgContainer};
    border-radius: ${token.borderRadiusLG}px;
  `,
}));

export default usePrStatsDashboardStyles;

