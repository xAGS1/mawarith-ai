import { notFound } from "next/navigation";
import { learningPaths } from "@/data/home";
import { PathShell } from "@/components/home/path-shell";

export function generateStaticParams() {
  return learningPaths.map(({ slug }) => ({ slug }));
}

export default async function PathPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const path = learningPaths.find((path) => path.slug === slug);
  if (!path) notFound();
  return <PathShell path={path} />;
}
