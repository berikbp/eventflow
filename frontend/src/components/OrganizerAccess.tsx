import { useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { verifyOrganizer } from "../api/events";
import { ErrorMessage } from "./Feedback";
import { Icon } from "./Icon";

export function OrganizerAccess({
  token,
  onToken,
  children,
}: {
  token: string;
  onToken: (token: string) => void;
  children: ReactNode;
}) {
  const [input, setInput] = useState("");
  const access = useMutation({
    mutationFn: verifyOrganizer,
    onSuccess: (_, checkedToken) => {
      onToken(checkedToken);
      setInput("");
    },
  });
  if (token) return children;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    access.mutate(input.trim());
  }
  return (
    <main>
      <Link className="breadcrumb" to="/">
        <Icon name="back" />
        Все мероприятия
      </Link>
      <div className="access-layout">
        <section className="access-copy">
          <h1>
            Вы собираете людей.
            <br />
            Мы собираем всё остальное.
          </h1>
          <p>
            Создайте событие, пригласите участников и встречайте гостей с
            готовыми билетами.
          </p>
          <ul className="access-benefits">
            <li>
              <Icon name="check" />
              Регистрация без переполнения
            </li>
            <li>
              <Icon name="check" />
              Очередь, которая движется сама
            </li>
            <li>
              <Icon name="check" />
              Билеты и проверка входа
            </li>
          </ul>
        </section>
        <form className="panel form" onSubmit={submit}>
          <h2>Вход организатора</h2>
          <p className="intro">
            Введите токен доступа, выданный администратором EventFlow.
          </p>
          <label>
            Токен организатора
            <input
              type="password"
              required
              autoComplete="off"
              placeholder="Ваш токен доступа"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </label>
          <ErrorMessage error={access.error} />
          <button disabled={access.isPending || !input.trim()}>
            {access.isPending ? "Проверяем…" : "Продолжить"}
            <Icon name="arrow" />
          </button>
          <p className="footnote">
            Токен действует в этой вкладке. После перезагрузки страницы
            потребуется войти снова.
          </p>
        </form>
      </div>
    </main>
  );
}
