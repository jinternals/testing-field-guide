package shop;

import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.*;

public interface OrderRepository extends JpaRepository<CustomerOrder, UUID> {
  Optional<CustomerOrder> findByReference(String reference);

  @Query("""
      select o from CustomerOrder o left join fetch o.lines
      where o.reference = :reference""")
  Optional<CustomerOrder> findWithLines(String reference);
}
