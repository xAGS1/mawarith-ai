import { ArrowUp } from "lucide-react";
import { Brand } from "@/components/ui/brand";
export function Footer() {
  return (
    <footer className="footer" id="about">
      <div className="container footer-main">
        <div>
          <Brand compact />
          <p className="footer-description">
            مساحة تعليمية لفهم علم المواريث في الإسلام.
            <br />
            للجميع، مهما كانت خلفيتك أو نقطة بدايتك.
          </p>
        </div>
        <div className="footer-links">
          <a href="#concepts">استكشف المفاهيم</a>
          <a href="#learning-path">المسار التعليمي</a>
          <a href="#examples">الأمثلة</a>
          <a href="#sources">المصادر</a>
        </div>
        <div className="footer-quote">
          بالعلم، نفهم.
          <br />
          <span>وبالفهم، نطمئن.</span>
        </div>
      </div>
      <div className="container footer-bottom">
        <p>
          <span lang="en" dir="ltr">
            © 2026 MAWARITH AI
          </span>{" "}
          — صُمّم من أجل الفهم
        </p>
        <span>التعلم أولًا .. والحساب خطوة تالية</span>
        <a href="#home" aria-label="العودة إلى أعلى الصفحة">
          <ArrowUp size={17} />
        </a>
      </div>
    </footer>
  );
}
