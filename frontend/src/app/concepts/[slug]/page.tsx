import { notFound } from "next/navigation";
import { curriculum } from "@/data/concept-curriculum";
import { ConceptLesson } from "@/components/concepts/concept-lesson";

export function generateStaticParams() {
  return curriculum.map(({ slug }) => ({ slug }));
}
export default async function ConceptPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const concept = curriculum.find((item) => item.slug === slug);
  if (!concept) notFound();
  return <ConceptLesson concept={concept} />;
}
