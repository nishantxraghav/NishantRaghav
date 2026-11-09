import { Fragment } from "react";

type MaskedTitleProps = {
  text: string;
  as?: "h1" | "h2" | "h3";
  id?: string;
  className?: string;
};

/** A title that rises from behind its own line, once, one line at a time. */
export function MaskedTitle({ text, as: Tag = "h2", id, className }: MaskedTitleProps) {
  return (
    <Tag id={id} data-reveal="title" className={className}>
      {text.split(" ").map((word, i) => (
        <Fragment key={i}>
          {i > 0 ? " " : null}
          <span className="title-word">
            <span className="title-inner">{word}</span>
          </span>
        </Fragment>
      ))}
    </Tag>
  );
}
