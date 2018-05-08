
import { CacheRequester, Loading } from './ajax';
import { Modal } from './layout';
import { queryConsumer } from './router';
import { sortAs, SortableTable } from './sorting';


export var ZoznamPrihlasenychNaTerminColumns = [
  ["Meno", 'plne_meno', sortAs.personName],
  ["Študijný program", 'sp_skratka'],
  ["Ročník", 'rocnik', sortAs.number],
  ["E-mail", 'email'],
  ["Dátum prihlásenia", 'datum_prihlasenia', sortAs.date]
];


function ZoznamPrihlasenychNaTerminModalContent() {
  return queryConsumer(query => {
    var cache = new CacheRequester();
    var {modalTerminKey} = query;

    if (!modalTerminKey) return null;
    var studenti = cache.get('get_prihlaseni_studenti', modalTerminKey);

    if (!studenti) {
      return <Loading requests={cache.missing} />;
    }

    var [studenti, header] = SortableTable(
      studenti, ZoznamPrihlasenychNaTerminColumns,
      query, 'modalStudentiSort');

    var message = studenti.length ? null : "Na termín nie sú prihlásení žiadni študenti.";

    return (
      <SortableTable
        items={studenti}
        columns={ZoznamPrihlasenychNaTerminColumns}
        queryKey="modalStudentiSort"
        row={(student) => (
          <tr>
            <td>{student.plne_meno}</td>
            <td>{student.sp_skratka}</td>
            <td>{student.rocnik}</td>
            <td>{student.email &&
                    <a href={"mailto:" + student.email}>{student.email}</a>}
            </td>
            <td>{student.datum_prihlasenia}</td>
          </tr>
        )}
        message={message}
      />
    );
  });
}

export function ZoznamPrihlasenychNaTerminModal() {
  return (
    <Modal title="Zoznam prihlásených na termín">
      <ZoznamPrihlasenychNaTerminModalContent />
    </Modal>
  );
}
