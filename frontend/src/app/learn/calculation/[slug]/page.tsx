import { notFound } from "next/navigation";
import { calculationPaths } from "@/data/calculation-paths";
import { CalculationLesson } from "@/components/calculation/calculation-lesson";
export function generateStaticParams() {
  return calculationPaths.map((path) => ({ slug: path.slug }));
}
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const path = calculationPaths.find((path) => path.slug === slug);
  if (!path) notFound();
  return <CalculationLesson path={path} />;
}
