'use client';

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { createStyles } from "antd-style";
import { debounce } from "@/lib/utils";

const useStyles = createStyles(({ css, token }) => ({
    popoverBox: css`
    position: absolute;
    z-index: 9999;
    background: ${token.colorBgElevated};
    border: 1px solid ${token.colorBorderSecondary};
    border-radius: ${token.borderRadiusLG}px;
    box-shadow: ${token.boxShadowSecondary};
    padding: 14px 20px;
    min-width: 220px;
    color: ${token.colorText};
    font-size: ${token.fontSize};
    line-height: 1.6;
    font-family: inherit;
    pointer-events: auto; /* ✅ popover可交互 */
  `,
}));

export default function CodeBlockWithPopover({ html }: { html: string }) {
    const containerRef = useRef<HTMLDivElement>(null);
    const popOverRef = useRef<HTMLDivElement>(null)
    const { styles } = useStyles();

    const [popover, setPopover] = useState<null | {
        x: number;
        y: number;
        info: {
            severity?: string;
            description?: string;
            recommendation?: string;
        };
        visible: boolean
    }>(null);

    // 记录当前是否处于 popover 区域内
    const isInsidePopover = useRef(false);

    useLayoutEffect(() => {
        if (!popover || !popOverRef.current) return;
        const height = popOverRef.current.offsetHeight;
        setPopover((prev) => prev && { ...prev, y: prev.y - height, visible: true });
    }, [popover?.info]);


    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        container.innerHTML = html;
        const unsafeLines = container.querySelectorAll(".code-unsafe");
        const handlers: { el: Element; show: (e: Event) => void; hide: () => void }[] = [];

        unsafeLines.forEach((line) => {
            const info = JSON.parse(line.getAttribute("data-info") || "{}");

            const show = debounce((e: Event) => {
                const rect = (e.target as HTMLElement).getBoundingClientRect();
                setPopover({
                    x: rect.left,
                    y: rect.top, // ✅ 出现在目标上方
                    info,
                    visible: false
                });
            }, 300);

            const hide = debounce(() => {
                // ✅ 若鼠标在popover中，不执行隐藏
                if (isInsidePopover.current) return;
                setPopover(null);
            }, 300);

            line.addEventListener("mouseenter", show);
            line.addEventListener("mouseleave", hide);
            handlers.push({ el: line, show, hide });
        });

        return () => {
            handlers.forEach(({ el, show, hide }) => {
                el.removeEventListener("mouseenter", show);
                el.removeEventListener("mouseleave", hide);
            });
        };
    }, [html]);


    return (
        <>
            <div ref={containerRef} className="prose" />
            {popover &&
                createPortal(
                    <div
                        ref={popOverRef}
                        className={styles.popoverBox}
                        style={{
                            top: popover.y,
                            left: popover.x,
                            visibility: popover.visible ? 'visible' : 'hidden'
                        }}
                        onMouseEnter={() => {
                            isInsidePopover.current = true;
                        }}
                        onMouseLeave={() => {
                            isInsidePopover.current = false;
                            setPopover(null);
                        }}
                    >
                        <div>
                            <b>Severity:</b>{" "}
                            <span style={{ color: "#cf1322" }}>
                                {popover.info?.severity || "Unknown"}
                            </span>
                            <br />
                            {popover.info?.description && (
                                <>
                                    <b>Description:</b> {popover.info.description}
                                    <br />
                                </>
                            )}
                            {popover.info?.recommendation && (
                                <>
                                    <b>Fix:</b> {popover.info.recommendation}
                                </>
                            )}
                        </div>
                    </div>,
                    document.body
                )}
        </>
    );
}
