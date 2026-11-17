import { upstream } from "../../../../../lib/upstream";
export function GET() { return upstream("/api/v1/system/info"); }
