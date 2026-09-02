import Link from "next/link";

export function BeheerNav() {
  return (
    <div className="mb-6 flex gap-4 text-sm font-medium text-gray-500">
      <Link href="/beheer" className="hover:text-brand">
        Dashboard
      </Link>
      <Link href="/beheer/spelers" className="hover:text-brand">
        Spelers
      </Link>
      <Link href="/beheer/wedstrijden" className="hover:text-brand">
        Wedstrijden
      </Link>
      <Link href="/beheer/import" className="hover:text-brand">
        Excel importeren
      </Link>
    </div>
  );
}
