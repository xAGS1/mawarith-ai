import {
  UsersRound,
  ChartPie,
  GitBranch,
  Split,
  ShieldHalf,
  Layers3,
  RotateCcw,
} from "lucide-react";
import type { Concept } from "@/data/home";
const icons = {
  users: UsersRound,
  chart: ChartPie,
  tree: GitBranch,
  split: Split,
  shield: ShieldHalf,
  layers: Layers3,
  return: RotateCcw,
};
export function ConceptIcon({
  name,
  className,
}: {
  name: Concept["icon"];
  className?: string;
}) {
  const Icon = icons[name];
  return <Icon className={className} aria-hidden="true" strokeWidth={1.6} />;
}
