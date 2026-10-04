import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { Hero } from "@/components/home/hero";
import { ConceptCards } from "@/components/home/concept-cards";
import { LearningPath } from "@/components/home/learning-path";
import { InteractiveExamples } from "@/components/home/interactive-examples";
import { Sources } from "@/components/home/sources";

export default function Home() {
  return (
    <>
      <Navbar />
      <main id="main">
        <Hero />
        <ConceptCards />
        <LearningPath />
        <InteractiveExamples />
        <Sources />
      </main>
      <Footer />
    </>
  );
}
