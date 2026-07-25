// Plain, colorless depth table — structural only (this is a wireframe, not a
// design task). Renders [price, quantity] levels.
export function DepthTable({
  title,
  levels,
}: {
  title: string;
  levels: string[][];
}) {
  return (
    <table className="border border-current text-sm">
      <thead>
        <tr>
          <th className="border border-current px-2 py-1" colSpan={2}>
            {title}
          </th>
        </tr>
        <tr>
          <th className="border border-current px-2 py-1 text-left">Price</th>
          <th className="border border-current px-2 py-1 text-left">Quantity</th>
        </tr>
      </thead>
      <tbody>
        {levels.length === 0 ? (
          <tr>
            <td className="border border-current px-2 py-1" colSpan={2}>
              —
            </td>
          </tr>
        ) : (
          levels.map((level, i) => (
            <tr key={i}>
              <td className="border border-current px-2 py-1 font-mono">{level[0]}</td>
              <td className="border border-current px-2 py-1 font-mono">{level[1]}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
