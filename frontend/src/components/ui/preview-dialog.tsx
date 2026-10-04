"use client";
import { useLocale } from "@/i18n/locale-context";
import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { ReactNode } from "react";
export function PreviewDialog({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const { t } = useLocale();
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className="preview-dialog"
      aria-labelledby="preview-title"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) ref.current?.close();
      }}
    >
      <button
        className="dialog-close"
        aria-label={t("إغلاق المعاينة")}
        onClick={() => ref.current?.close()}
      >
        <X size={20} />
      </button>
      <span className="eyebrow">{t("اكتشف خطوة جديدة")}</span>
      <h2 id="preview-title">{title}</h2>
      {children}
    </dialog>
  );
}
