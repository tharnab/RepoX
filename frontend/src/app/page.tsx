import { Header } from "@/components/header";
import { Chat } from "@/components/chat";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-950">
      <Header />
      <Chat />
    </div>
  );
}