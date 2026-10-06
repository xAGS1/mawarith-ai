"use client";
import type { ReactNode } from "react";
import { useLocale } from "@/i18n/locale-context";
import type { SourceRecord } from "@/lib/ask/types";

/** Integer arithmetic only; the percentage is decorative, never a share. */
export function visualShare(fraction: string, count: number): number | null {
  const match = /^(\d+)(?:\/(\d+))?$/.exec(fraction);
  if (
    !match ||
    !Number.isSafeInteger(count) ||
    count < 1 ||
    fraction.length > 80
  )
    return null;
  const numerator = BigInt(match[1]) * BigInt(count);
  const denominator = BigInt(match[2] || "1");
  if (denominator === BigInt(0) || numerator > denominator) return null;
  return Number((numerator * BigInt(10000)) / denominator) / 100;
}
export function CaseUnderstanding({
  relatives,
}: {
  relatives: SourceRecord[];
}) {
  const { t } = useLocale();
  if (!relatives.length) return null;
  return (
    <div className="case-understanding">
      <h4>{t({ ar: "فهمت الحالة هكذا", en: "Case understood as" })}</h4>
      <div className="case-relation-chips">
        {relatives.map((relative, i) => (
          <span key={i}>
            {String(relative.relation)} <bdi>×{Number(relative.count)}</bdi>
          </span>
        ))}
      </div>
    </div>
  );
}
export function ReadyResult({
  children,
  rows,
  verification,
  relatives,
  verified,
}: {
  children: ReactNode;
  rows: SourceRecord[];
  verification: SourceRecord | null;
  relatives: SourceRecord[];
  verified: boolean;
}) {
  const { t } = useLocale();
  const widths = rows.map((row) =>
    visualShare(String(row.per_head_shares), Number(row.count)),
  );
  return (
    <div className="ready-result">
      <CaseUnderstanding relatives={relatives} />
      {verified && (
        <div className="ask-distribution">
          <h4>
            {t({
              ar: "التوزيع المتحقق حسابيًا",
              en: "Arithmetically verified distribution",
            })}
          </h4>
          {widths.every((width) => width !== null) && (
            <div className="distribution-bar" aria-hidden="true">
              {widths.map((width, i) => (
                <span key={i} style={{ width: String(width) + "%" }} />
              ))}
            </div>
          )}
          <div className="ask-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{t({ ar: "الوارث", en: "Heir" })}</th>
                  <th>{t({ ar: "العدد", en: "Count" })}</th>
                  <th>{t({ ar: "نصيب الفرد", en: "Share per individual" })}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    <td>{String(row.heir)}</td>
                    <td>{Number(row.count)}</td>
                    <td dir="ltr">
                      <strong>{String(row.per_head_shares)}</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="verification-summary">
            {t({ ar: "المجموع", en: "Total" })} ={" "}
            <bdi>{String(verification?.total_fraction)}</bdi> ✓{" "}
            <span>
              {t({ ar: "متسق حسابيًا", en: "Arithmetically consistent" })}
            </span>
          </p>
        </div>
      )}
      {children}
    </div>
  );
}
