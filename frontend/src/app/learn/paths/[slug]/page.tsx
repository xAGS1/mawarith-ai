import { notFound } from "next/navigation";
import { learningPathCurriculum } from "@/data/learning-paths";
import { PathShell } from "@/components/home/path-shell";

export function generateStaticParams() {
  return learningPathCurriculum.map(({ slug }) => ({ slug }));
}

export default async function PathPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const path = learningPathCurriculum.find((path) => path.slug === slug);
  if (!path) notFound();
  return <PathShell path={path} />;
}
