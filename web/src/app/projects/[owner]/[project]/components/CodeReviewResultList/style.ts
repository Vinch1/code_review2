import { createStyles } from "antd-style";

const useCodeReviewResultListStyles = createStyles(({ css, token }) => ({
  avatar: css`
    width: ${token.sizeSM}px;
    height: ${token.sizeSM}px;
  `,
  listItemContent: css`
    gap: ${token.paddingXXS}px;
    width: 80%;
  `,
  listItem: css`
    padding-left: ${token.padding}px !important;
  `,
  listItemFlex: css`
    gap: ${token.paddingXXS}px;
    width: 100%;
    align-items: center;
  `,
  buttonDanger: css`
    align-items: center;
    background-color: initial;
    border-radius: 624.9375rem;
    border-style: solid;
    border-width: 0.0625rem;
    border-color: ${token.colorError} !important;
    color: ${token.colorError} !important;
    display: inline-flex;
    font-size:${token.fontSize}px;
    font-weight: 500;
    line-height: 1;
    padding: 0px ${token.paddingXXS}px;
    white-space: nowrap;
    height:${token.sizeLG}px;
  `,
  buttonSafe: css`
    align-items: center;
    background-color: initial;
    border-radius: 624.9375rem;
    border-style: solid;
    border-width: 0.0625rem;
    border-color: #1f883d !important;
    color: #1f883d !important;
    display: inline-flex;
    font-size:${token.fontSize}px;
    font-weight: 500;
    line-height: 1;
    padding: 0px ${token.paddingXXS}px;
    white-space: nowrap;
    height:${token.sizeLG}px;
  `,

}));

export default useCodeReviewResultListStyles;