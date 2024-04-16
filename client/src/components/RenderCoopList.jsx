import React from 'react';
import ListGroup from 'react-bootstrap/ListGroup';
import ListGroupItem from 'react-bootstrap/ListGroupItem';
import { PencilSquare } from 'react-bootstrap-icons';
import { Link } from 'react-router-dom';

const RenderCoopList = (props) => {
  const formatAddress = (obj) => {
    const streetAdd = obj.street_address;
    const cityName = obj.city;
    const stateCode = obj.state;
    const zip = obj.postal_code;

    return streetAdd + ', ' + cityName + ', ' + stateCode + ' ' + zip;
  };

  return (
    <>
      <br />
      <ListGroup variant="flush">
        <ListGroupItem key="header">
          <h3 className="float-left font-weight-bold">{props.columnOneText}</h3>
          <h3 className="float-right font-weight-bold">
            {props.columnTwoText}
          </h3>
        </ListGroupItem>
        {props.searchResults.map((item) => (
          <ListGroupItem key={item.id} value={item.name}>
            <div className="float-left">
              {item.name}
              <br />
              {formatAddress(item.addresses[0].address)}
            </div>
            <span className="float-right">
              <Link to={props.link + item.id}>
                <PencilSquare color="royalblue" size={26} />
              </Link>
            </span>
          </ListGroupItem>
        ))}
      </ListGroup>
    </>
  );
};

export default RenderCoopList;
