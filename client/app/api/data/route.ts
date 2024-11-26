import { NextResponse } from "next/server";
import { getData } from "@/lib/getData";

export const runtime = "edge";

export async function GET() {
  const data = await getData();

  if (data === null) {
    return NextResponse.json({ error: "File not found" }, { status: 404 });
  }

  return NextResponse.json({
    ...data,
  });
}
