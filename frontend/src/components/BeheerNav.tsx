import Link from "next/link";

export function BeheerNav() {
  return (
    <div className="mb-6 flex flex-wrap gap-x-4 gap-y-2 text-sm font-medium text-gray-500">
      <Link href="/beheer" className="hover:text-brand">
        Dashboard
      </Link>
      <Link href="/beheer/spelers" className="hover:text-brand">
        Spelers
      </Link>
      <Link href="/beheer/wedstrijden" className="hover:text-brand">
        Wedstrijden
      </Link>
      <Link href="/beheer/seizoenen" className="hover:text-brand">
        Seizoenen
      </Link>
      <Link href="/beheer/teambeheer" className="hover:text-brand">
        Teambeheer
      </Link>
      <Link href="/beheer/logboek" className="hover:text-brand">
        Logboek
      </Link>
      <Link href="/beheer/statistieken" className="hover:text-brand">
        Statistieken
      </Link>
      <Link href="/beheer/instellingen" className="hover:text-brand">
        Instellingen
      </Link>
    </div>
  );
}
